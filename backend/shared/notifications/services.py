import logging
from typing import Optional
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Notification, NotificationPreference

logger = logging.getLogger("shared.notifications")


class NotificationService:
    def send_notification(
        self,
        recipient,
        title: str,
        body: str = "",
        channel: str = Notification.Channel.IN_APP,
        priority: str = Notification.Priority.MEDIUM,
        action_url: str = "",
        icon: str = "",
        instance=None,
        metadata: Optional[dict] = None,
    ) -> Notification:
        kwargs = {
            "recipient": recipient,
            "title": title,
            "body": body,
            "channel": channel,
            "priority": priority,
            "action_url": action_url,
            "icon": icon,
            "metadata": metadata or {},
        }
        if instance is not None:
            kwargs["content_type"] = ContentType.objects.get_for_model(instance)
            kwargs["object_id"] = instance.pk
        notif = Notification.objects.create(**kwargs)

        # Dispatch real email if channel is EMAIL and user has email
        if channel == Notification.Channel.EMAIL and recipient.email:
            self._dispatch_email(notif, recipient)

        logger.info(
            "Notification %s envoyée à %s via %s: %s",
            priority, recipient, channel, title,
        )
        return notif

    def _dispatch_email(self, notif, recipient):
        """Render and send notification email asynchronously."""
        from .tasks import send_notification_email

        ctx = {
            "title": notif.title,
            "body": notif.body,
            "priority": notif.priority,
            "action_url": notif.action_url or "",
            "action_label": "Voir les détails",
            "recipient_name": recipient.get_full_name() or recipient.email,
            "settings_url": f"{settings.SITE_URL or ''}/settings/notifications",
        }
        html_body = render_to_string("email/notification.html", ctx)
        text_body = render_to_string("email/notification.txt", ctx)

        send_notification_email.delay(
            recipient_email=recipient.email,
            subject=notif.title,
            body=text_body,
            html_body=html_body,
            priority=notif.priority,
            action_url=notif.action_url or "",
            recipient_name=recipient.get_full_name() or "",
        )

    def notify_admins(
        self,
        title: str,
        body: str = "",
        priority: str = Notification.Priority.MEDIUM,
        action_url: str = "",
        icon: str = "",
        instance=None,
        metadata: Optional[dict] = None,
    ):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admins = User.objects.filter(
            is_staff=True, is_active=True,
            notification_preferences__email_alerts=True,
        )
        for admin in admins:
            prefs, _ = NotificationPreference.objects.get_or_create(user=admin)
            ch = Notification.Channel.EMAIL if prefs.email_alerts else Notification.Channel.IN_APP
            self.send_notification(
                recipient=admin, title=title, body=body,
                channel=ch,
                priority=priority, action_url=action_url, icon=icon,
                instance=instance, metadata=metadata,
            )

    def notify_gestionnaires(
        self,
        title: str,
        body: str = "",
        priority: str = Notification.Priority.MEDIUM,
        action_url: str = "",
        icon: str = "",
        instance=None,
        metadata: Optional[dict] = None,
    ):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        User = get_user_model()
        gestionnaires = User.objects.filter(
            is_active=True,
            groups__name="Gestionnaire",
        )
        for user in gestionnaires:
            prefs, _ = NotificationPreference.objects.get_or_create(user=user)
            ch = Notification.Channel.EMAIL if prefs.email_alerts else Notification.Channel.IN_APP
            self.send_notification(
                recipient=user, title=title, body=body,
                channel=ch,
                priority=priority, action_url=action_url, icon=icon,
                instance=instance, metadata=metadata,
            )

    @transaction.atomic
    def mark_as_read(self, notification_id: int, user) -> Optional[Notification]:
        try:
            notif = Notification.objects.get(id=notification_id, recipient=user)
            notif.mark_as_read()
            return notif
        except Notification.DoesNotExist:
            logger.warning("Notification %s introuvable pour %s", notification_id, user)
            return None

    def get_unread_count(self, user) -> int:
        return Notification.objects.filter(recipient=user, is_read=False).count()

    def get_unread_high_priority(self, user):
        return Notification.objects.filter(
            recipient=user, is_read=False,
            priority__in=[Notification.Priority.HIGH, Notification.Priority.CRITICAL],
        )


notification_service = NotificationService()
