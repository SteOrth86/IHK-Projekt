from email.message import EmailMessage

from kube_app_provisioner.services.apps import email as email_service
from kube_app_provisioner.core.storage import Instance


def test_build_wordpress_access_email_contains_url_and_admin_user():
    instance = Instance(
        id="wp-test",
        type="wordpress",
        namespace="wp-test",
        domain="kunde-email-test.example.test",
        status="running",
        created_at="2025-11-26T12:00:00Z",
        updated_at="2025-11-26T12:00:00Z",
    )

    msg: EmailMessage = email_service._build_wordpress_access_email(
        instance,
        to_address="kunde@example.test",
    )

    body = msg.get_content()
    assert "https://kunde-email-test.example.test/wp-admin" in body
    assert "Benutzername: admin" in body
