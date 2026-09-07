import random
import uuid
from datetime import datetime

from jinja2 import Template

from CTFd.utils import get_config
from CTFd.models import db
from CTFd.plugins.dynamic_challenges import DynamicChallenge


class WhaleConfig(db.Model):
    key = db.Column(db.String(length=128), primary_key=True)
    value = db.Column(db.Text)

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return "<WhaleConfig {0} {1}>".format(self.key, self.value)


class WhaleRedirectTemplate(db.Model):
    key = db.Column(db.String(20), primary_key=True)
    frp_template = db.Column(db.Text)
    access_template = db.Column(db.Text)

    def __init__(self, key, access_template, frp_template):
        self.key = key
        self.access_template = access_template
        self.frp_template = frp_template

    def __repr__(self):
        return "<WhaleRedirectTemplate {0}>".format(self.key)


class DynamicDockerChallenge(DynamicChallenge):
    __mapper_args__ = {"polymorphic_identity": "dynamic_docker"}
    id = db.Column(
        db.Integer, db.ForeignKey("dynamic_challenge.id", ondelete="CASCADE"), primary_key=True
    )

    memory_limit = db.Column(db.Text, default="128m")
    cpu_limit = db.Column(db.Float, default=0.5)
    dynamic_score = db.Column(db.Integer, default=0)

    docker_image = db.Column(db.Text, default=0)
    redirect_type = db.Column(db.Text, default=0)
    redirect_port = db.Column(db.Integer, default=0)
    redirect_rules = db.Column(db.Text, default="")

    def __init__(self, *args, **kwargs):
        kwargs["initial"] = kwargs["value"]
        super(DynamicDockerChallenge, self).__init__(**kwargs)


class WhaleContainer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(None, db.ForeignKey("users.id"))
    challenge_id = db.Column(None, db.ForeignKey("challenges.id"))
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    renew_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.Integer, default=1)
    uuid = db.Column(db.String(256))
    port = db.Column(db.Integer, nullable=True, default=0)
    ports = db.Column(db.JSON, nullable=True, default=lambda: {})
    flag = db.Column(db.String(128), nullable=False)

    # Relationships
    user = db.relationship(
        "Users", foreign_keys="WhaleContainer.user_id", lazy="select")
    challenge = db.relationship(
        "DynamicDockerChallenge", foreign_keys="WhaleContainer.challenge_id", lazy="select"
    )

    @property
    def http_subdomain(self):
        return Template(get_config(
            'whale:template_http_subdomain', '{{ container.uuid }}'
        )).render(container=self)

    def __init__(self, user_id, challenge_id):
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.start_time = datetime.now()
        self.renew_count = 0
        self.uuid = str(uuid.uuid4())
        self.flag = Template(get_config(
            'whale:template_chall_flag', '{{ "flag{"+uuid.uuid4()|string+"}" }}'
        )).render(container=self, uuid=uuid, random=random, get_config=get_config)

    @property
    def user_access(self):
        if self.challenge.redirect_rules:
            access_strs = []
            rules = [r.strip() for r in self.challenge.redirect_rules.split(",") if r.strip()]
            for rule in rules:
                if "/" in rule:
                    port, rtype = rule.split("/", 1)
                    template = WhaleRedirectTemplate.query.filter_by(key=rtype).first()
                    if template:
                        # For direct type, we use the allocated port for this specific internal port
                        # The template might use container.port, but we can override it temporarily
                        # or just let the template render and we replace it, or better, pass port mapping
                        original_port = self.port
                        if rtype == "direct" and self.ports and port in self.ports:
                            self.port = self.ports[port]
                        
                        rendered = Template(template.access_template).render(container=self, get_config=get_config, rule_port=port)
                        access_strs.append(rendered)
                        
                        self.port = original_port
            return "<br>".join(access_strs)

        return Template(WhaleRedirectTemplate.query.filter_by(
            key=self.challenge.redirect_type
        ).first().access_template).render(container=self, get_config=get_config)

    @property
    def frp_config(self):
        if self.challenge.redirect_rules:
            config_strs = []
            rules = [r.strip() for r in self.challenge.redirect_rules.split(",") if r.strip()]
            for rule in rules:
                if "/" in rule:
                    port, rtype = rule.split("/", 1)
                    template = WhaleRedirectTemplate.query.filter_by(key=rtype).first()
                    if template:
                        original_port = self.port
                        if rtype == "direct" and self.ports and port in self.ports:
                            self.port = self.ports[port]
                            
                        # FRP config template usually uses container.uuid, we need to append the port to avoid duplicate names
                        rendered = Template(template.frp_template).render(container=self, get_config=get_config)
                        # Quick hack: replace the rule name [rtype_userid_uuid] with [rtype_userid_uuid_port]
                        rule_name_prefix = f"[{rtype}_{self.user_id}_{self.uuid}"
                        if rule_name_prefix + "]" in rendered:
                            rendered = rendered.replace(rule_name_prefix + "]", rule_name_prefix + f"_{port}]")
                        
                        config_strs.append(rendered)
                        self.port = original_port
            return "\n".join(config_strs)

        return Template(WhaleRedirectTemplate.query.filter_by(
            key=self.challenge.redirect_type
        ).first().frp_template).render(container=self, get_config=get_config)

    def __repr__(self):
        return "<WhaleContainer ID:{0} {1} {2} {3} {4}>".format(self.id, self.user_id, self.challenge_id,
                                                                self.start_time, self.renew_count)
