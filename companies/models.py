from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


company_id_validator = RegexValidator(
    regex=r"^[A-Za-z0-9_-]+$",
    message=(
        "Идентификатор компании может содержать только "
        "латинские буквы, цифры, дефис и подчёркивание."
    ),
)


class CompanyAccess(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="company_accesses",
        verbose_name="Пользователь",
    )

    company_id = models.CharField(
        "ID компании в TitanRetail",
        max_length=100,
        validators=[company_id_validator],
    )

    company_name = models.CharField(
        "Название компании",
        max_length=255,
        blank=True,
    )

    is_active = models.BooleanField(
        "Доступ разрешён",
        default=True,
    )

    class Meta:
        verbose_name = "доступ к компании"
        verbose_name_plural = "доступы к компаниям"
        ordering = ("company_name", "company_id")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "company_id"),
                name="unique_user_company_access",
            ),
        ]

    def __str__(self) -> str:
        name = self.company_name or self.company_id
        return f"{self.user.username}: {name}"