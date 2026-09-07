/**
 * CTFd Account Provisioning Plugin - Frontend JavaScript
 * Handles file upload, preview display, account provisioning, and document download.
 */

(function () {
    "use strict";

    // State
    let previewToken = null;
    let currentLang = document.getElementById("lang_select") ? document.getElementById("lang_select").value : "en";

    // DOM Elements
    const uploadForm = document.getElementById("upload-form");
    const uploadBtn = document.getElementById("upload-btn");
    const csvFile = document.getElementById("csv_file");
    const emailDomain = document.getElementById("email_domain");
    const langSelect = document.getElementById("lang_select");
    const errorAlert = document.getElementById("error-alert");
    const errorMessage = document.getElementById("error-message");
    const loading = document.getElementById("loading");
    const previewSection = document.getElementById("preview-section");
    const previewTbody = document.getElementById("preview-tbody");
    const totalCount = document.getElementById("total-count");
    const validCount = document.getElementById("valid-count");
    const invalidCount = document.getElementById("invalid-count");
    const confirmBtn = document.getElementById("confirm-btn");
    const cancelBtn = document.getElementById("cancel-btn");
    const resultsSection = document.getElementById("results-section");
    const resultsTbody = document.getElementById("results-tbody");
    const resultMessage = document.getElementById("result-message");
    const downloadBtn = document.getElementById("download-btn");

    // Get CSRF nonce from the hidden form field
    function getNonce() {
        const nonceInput = document.querySelector('input[name="nonce"]');
        return nonceInput ? nonceInput.value : "";
    }

    // Show error alert
    function showError(message) {
        errorMessage.textContent = message;
        errorAlert.classList.remove("d-none");
        previewSection.classList.add("d-none");
        loading.classList.add("d-none");
    }

    // Hide error alert
    function hideError() {
        errorAlert.classList.add("d-none");
    }

    // Show loading spinner
    function showLoading() {
        loading.classList.remove("d-none");
        hideError();
        previewSection.classList.add("d-none");
        resultsSection.classList.add("d-none");
    }

    // Hide loading spinner
    function hideLoading() {
        loading.classList.add("d-none");
    }

    // Language change handler - reload page with new language
    if (langSelect) {
        langSelect.addEventListener("change", function () {
            const newLang = this.value;
            const url = new URL(window.location.href);
            url.searchParams.set("lang", newLang);
            window.location.href = url.toString();
        });
    }

    // Handle file upload
    if (uploadForm) {
        uploadForm.addEventListener("submit", function (e) {
            e.preventDefault();

            if (!csvFile.files.length) {
                showError("Please select a file.");
                return;
            }

            const file = csvFile.files[0];
            if (!file.name.toLowerCase().endsWith(".csv")) {
                showError("Please select a valid .csv file.");
                return;
            }

            showLoading();
            uploadBtn.disabled = true;

            const formData = new FormData();
            formData.append("file", file);
            formData.append("nonce", getNonce());
            formData.append("email_domain", emailDomain.value || "ctf.local");
            formData.append("lang", langSelect ? langSelect.value : "en");

            fetch("/plugins/ctfd-account-provisioning/admin/upload", {
                method: "POST",
                body: formData,
            })
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    hideLoading();
                    uploadBtn.disabled = false;

                    if (!data.success) {
                        showError(data.error || "Upload failed.");
                        return;
                    }

                    // Store preview token
                    previewToken = data.token;

                    // Update summary counts
                    totalCount.textContent = data.total_count;
                    validCount.textContent = data.valid_count;
                    invalidCount.textContent = data.invalid_count;

                    // Populate preview table
                    previewTbody.innerHTML = "";
                    var idx = 1;
                    data.participants.forEach(function (p) {
                        var row = document.createElement("tr");
                        if (p.status === "invalid") {
                            row.classList.add("table-danger");
                        }

                        var statusBadge = p.status === "valid"
                            ? '<span class="badge bg-success">✓</span>'
                            : '<span class="badge bg-danger" title="' + escapeHtml(p.error) + '">✗ ' + escapeHtml(p.error) + '</span>';

                        row.innerHTML =
                            '<td>' + idx + '</td>' +
                            '<td><strong>' + escapeHtml(p.name) + '</strong></td>' +
                            '<td><code>' + escapeHtml(p.username) + '</code></td>' +
                            '<td><small>' + escapeHtml(p.email) + '</small></td>' +
                            '<td><code>' + escapeHtml(p.password) + '</code></td>' +
                            '<td>' + statusBadge + '</td>';

                        previewTbody.appendChild(row);
                        idx++;
                    });

                    // Show preview section
                    previewSection.classList.remove("d-none");
                    resultsSection.classList.add("d-none");

                    // Enable/disable confirm button based on valid count
                    confirmBtn.disabled = data.valid_count === 0;
                })
                .catch(function (error) {
                    hideLoading();
                    uploadBtn.disabled = false;
                    showError("Network error: " + error.message);
                });
        });
    }

    // Handle cancel
    if (cancelBtn) {
        cancelBtn.addEventListener("click", function () {
            previewSection.classList.add("d-none");
            if (previewToken) {
                fetch("/plugins/ctfd-account-provisioning/admin/preview/" + previewToken, {
                    method: "DELETE", headers: {"CSRF-Token": getNonce(), "Content-Type": "application/json"}, body: "{}"
                }).catch(function () { /* TTL still guarantees expiry. */ });
            }
            previewToken = null;
            csvFile.value = "";
        });
    }

    // Handle confirm (provision accounts)
    if (confirmBtn) {
        confirmBtn.addEventListener("click", function () {
            if (!previewToken) {
                showError("No preview data. Please upload a file first.");
                return;
            }

            var validCountVal = parseInt(validCount.textContent, 10);
            if (!confirm("Create " + validCountVal + " accounts?")) {
                return;
            }

            showLoading();
            confirmBtn.disabled = true;
            cancelBtn.disabled = true;

            fetch("/plugins/ctfd-account-provisioning/admin/provision", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "CSRF-Token": getNonce(),
                },
                body: JSON.stringify({
                    token: previewToken,
                    lang: langSelect ? langSelect.value : "en",
                }),
            })
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    hideLoading();
                    previewSection.classList.add("d-none");

                    if (!data.success) {
                        showError(data.error || "Provisioning failed.");
                        confirmBtn.disabled = false;
                        cancelBtn.disabled = false;
                        return;
                    }

                    // Show results
                    resultsTbody.innerHTML = "";

                    // Display result message
                    resultMessage.textContent = data.message;
                    if (data.total_failed === 0) {
                        resultMessage.className = "alert alert-success mb-3";
                    } else if (data.total_success > 0) {
                        resultMessage.className = "alert alert-warning mb-3";
                    } else {
                        resultMessage.className = "alert alert-danger mb-3";
                    }

                    // Populate successful accounts
                    var idx = 1;
                    data.successful.forEach(function (s) {
                        var row = document.createElement("tr");
                        row.classList.add("table-success");
                        row.innerHTML =
                            '<td>' + idx + '</td>' +
                            '<td><strong>' + escapeHtml(s.name) + '</strong></td>' +
                            '<td><code>' + escapeHtml(s.username) + '</code></td>' +
                            '<td><small>' + escapeHtml(s.email) + '</small></td>' +
                            '<td><span class="badge bg-success">✓ Created</span></td>';
                        resultsTbody.appendChild(row);
                        idx++;
                    });

                    // Populate failed accounts
                    data.failed.forEach(function (f) {
                        var row = document.createElement("tr");
                        row.classList.add("table-danger");
                        var errorStr = Object.values(f.errors).flat().join(", ");
                        row.innerHTML =
                            '<td>' + idx + '</td>' +
                            '<td><strong>' + escapeHtml(f.name) + '</strong></td>' +
                            '<td><code>' + escapeHtml(f.username) + '</code></td>' +
                            '<td><small>' + escapeHtml(f.email) + '</small></td>' +
                            '<td><span class="badge bg-danger" title="' + escapeHtml(errorStr) + '">✗ Failed</span></td>';
                        resultsTbody.appendChild(row);
                        idx++;
                    });

                    // Show download button if there are successful accounts
                    if (data.doc_token) {
                        downloadBtn.href = "/plugins/ctfd-account-provisioning/admin/download/" + data.doc_token;
                        downloadBtn.classList.remove("d-none");
                    } else {
                        downloadBtn.classList.add("d-none");
                    }

                    resultsSection.classList.remove("d-none");
                    previewToken = null;
                    confirmBtn.disabled = false;
                    cancelBtn.disabled = false;
                })
                .catch(function (error) {
                    hideLoading();
                    confirmBtn.disabled = false;
                    cancelBtn.disabled = false;
                    showError("Network error: " + error.message);
                });
        });
    }

    // HTML escape utility
    function escapeHtml(text) {
        if (!text) return "";
        var div = document.createElement("div");
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }
})();
