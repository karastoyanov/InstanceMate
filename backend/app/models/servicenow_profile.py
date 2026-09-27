from datetime import datetime, timezone

from app.extensions import db


class ServiceNowProfile(db.Model):
    __tablename__ = "servicenow_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label = db.Column(db.String(100), nullable=False)
    instance_url = db.Column(db.String(255), nullable=False)
    auth_type = db.Column(db.String(20), nullable=False)
    # Fernet-encrypted JSON blob (keyed from SESSION_SECRET) holding whatever
    # this profile needs to authenticate - OAuth client id/secret + tokens,
    # or a basic-auth username/password. Never included in to_public_dict().
    credentials_encrypted = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "instance_url": self.instance_url,
            "auth_type": self.auth_type,
        }
