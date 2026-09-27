from datetime import datetime, timezone

from app.extensions import db


class LlmProfile(db.Model):
    __tablename__ = "llm_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label = db.Column(db.String(100), nullable=False)
    provider = db.Column(db.String(20), nullable=False)
    # Fernet-encrypted JSON blob (keyed from SESSION_SECRET) holding the API
    # key. Never included in to_public_dict().
    credentials_encrypted = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "provider": self.provider,
        }
