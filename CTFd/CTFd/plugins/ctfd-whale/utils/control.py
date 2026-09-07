import datetime
import traceback

from flask import current_app
from CTFd.plugins._lifecycle import lifecycle_lock
from CTFd.utils import get_config
from .cache import CacheProvider
from .db import DBContainer, db
from .docker import DockerUtils
from .routers import Router


class ControlUtil:
    @staticmethod
    def try_add_container(user_id, challenge_id):
        with lifecycle_lock("whale-routing"):
            db.session.rollback()  # refresh a snapshot opened before the lock
            if DBContainer.get_current_containers(user_id):
                return False, 'Existing instance cleanup is not complete. Please retry.'
            limit = int(get_config("whale:docker_max_container_count", 1000))
            if int(DBContainer.get_all_alive_container_count()) > limit:
                return False, 'Max container count exceed.'
            container = DBContainer.create_container_record(user_id, challenge_id)
            try:
                DockerUtils.add_container(container)
                ok, msg = Router.register(container)
                if ok:
                    container.status = 1
                    db.session.commit()
                    return True, 'Container created'
            except Exception:
                print(traceback.format_exc())
                db.session.rollback()
                msg = 'Container creation failed'
            # Retain a recovery record when routing/Docker cleanup is uncertain.
            container.status = -1
            db.session.commit()
            ControlUtil.try_remove_container(user_id)
            return False, msg

    @staticmethod
    def try_remove_container(user_id, expired_only=False):
        with lifecycle_lock("whale-routing"):
            db.session.rollback()
            container = DBContainer.get_current_containers(user_id=user_id)
            if not container:
                return False, 'No such container'
            if expired_only and container.status == 1:
                timeout = int(get_config('whale:docker_timeout', 3600))
                if container.start_time >= datetime.datetime.now() - datetime.timedelta(seconds=timeout):
                    return False, 'Instance is no longer expired'
            for _ in range(3):
                try:
                    ok, msg = Router.unregister(container)
                    if not ok:
                        return False, msg
                    DockerUtils.remove_container(container)
                    db.session.delete(container)
                    db.session.commit()
                    return True, 'Container destroyed'
                except Exception:
                    print(traceback.format_exc())
                    db.session.rollback()
            container.status = -1
            db.session.commit()
            return False, 'Failed when destroying instance, please contact admin!'

    @staticmethod
    def try_renew_container(user_id):
        container = DBContainer.get_current_containers(user_id)
        if not container:
            return False, 'No such container'
        timeout = int(get_config("whale:docker_timeout", "3600"))
        container.start_time = container.start_time + \
                               datetime.timedelta(seconds=timeout)
        if container.start_time > datetime.datetime.now():
            container.start_time = datetime.datetime.now()
            # race condition? useless maybe?
            # useful when docker_timeout < poll timeout (10 seconds)
            # doesn't make any sense
        else:
            return False, 'Invalid container'
        container.renew_count += 1
        db.session.commit()
        return True, 'Container Renewed'
