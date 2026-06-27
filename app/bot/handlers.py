from telethon import events
from app.schemas.lead import LeadIn
from app.services.storage import LeadStore
from app.services.scoring import score_lead
from app.services.router import route_lead
from app.ai.generator import AIGenerator

class MessageHandler:
    def __init__(self, client, config, ai: AIGenerator, store: LeadStore):
        self.client = client
        self.config = config
        self.ai = ai
        self.store = store
        self.app_cfg = config.get("app", {})
        self.forward_channel_link = self.app_cfg.get("bot", {}).get("forward_channel_link")
        self._forward_channel = None  # Resolved lazily

    async def handle_new_message(self, event):
        if event.out:
            return

        user = await event.get_sender()
        if user.bot or user.is_self:
            return

        lead = LeadIn(
            telegram_user_id=str(user.id),
            telegram_handle=user.username,
            display_name=user.first_name,
            language=getattr(user, "lang_code", None),
            message_text=event.raw_text or "",
        )

        # Get stored lead if exists (for follow-up context)
        stored = self.store.get_lead(lead.telegram_user_id)

        # Score the message
        score_delta, tags = score_lead(lead.message_text, self.config.get("scoring", {}))
        old_score = stored["score"] if stored else 0
        new_score = max(0, min(100, old_score + score_delta))

        # Route based on score
        route_status, next_action = route_lead(new_score, self.config)

        # Prepare lead context for AI
        lead_context = {
            "telegram_user_id": lead.telegram_user_id,
            "telegram_handle": lead.telegram_handle,
            "display_name": lead.display_name,
            "last_message_text": lead.message_text,
            "status": route_status,
            "score": new_score,
            "tags": tags,
        }

        # Generate AI response if available
        if self.ai:
            try:
                ai_output = await self.ai.generate(
                    lead_context=lead_context,
                    scripts=self.config.get("scripts", {}),
                    route_info={
                        "status": route_status,
                        "next_action": next_action,
                        "score": new_score,
                        "old_score": old_score,
                    },
                )
                reply_text = ai_output.reply_text
                final_status = ai_output.status
                final_tags = ai_output.tags or tags
                final_score = new_score + ai_output.score_delta
                final_score = max(0, min(100, final_score))
            except Exception as e:
                print(f"AI error: {e}, using fallback")
                reply_text = self._get_fallback_reply(route_status)
                final_status = route_status
                final_tags = tags
                final_score = new_score
        else:
            reply_text = self._get_fallback_reply(route_status)
            final_status = route_status
            final_tags = tags
            final_score = new_score

        # Save to database
        self.store.upsert(lead, final_status, final_score, final_tags)

        # Send reply
        if reply_text.strip():
            await event.reply(reply_text)

        # Forward hot leads to the channel
        if final_score >= self.config.get("scoring", {}).get("book_call_threshold", 80):
            await self._forward_hot_lead(event, lead, final_score, final_tags)

    async def _forward_hot_lead(self, event, lead, score, tags):
        """Forward a hot lead to the test channel."""
        if not self.forward_channel_link:
            return

        try:
            # Resolve channel entity lazily and cache it
            if self._forward_channel is None:
                self._forward_channel = await self.client.get_entity(self.forward_channel_link)

            # Forward the original message detail
            await self.client.send_message(
                self._forward_channel,
                f"🔥 **LEAD CHAUD — Score: {score}/100**\n\n"
                f"👤 **{lead.display_name or 'Inconnu'}**"
                f"{' (@' + lead.telegram_handle + ')' if lead.telegram_handle else ''}\n"
                f"🆔 {lead.telegram_user_id}\n\n"
                f"💬 **Message :**\n{lead.message_text[:500]}\n\n"
                f"🏷️ Tags : `{'`, `'.join(tags[-5:])}`\n"
                f"📊 Score : {score}/100\n"
                f"⏰ {event.date.strftime('%H:%M %d/%m/%Y')}",
                parse_mode="md",
            )
            print(f"  🔥 Hot lead forwarded to channel: {lead.telegram_user_id}")
        except Exception as e:
            print(f"  ❌ Failed to forward lead: {e}")

    def _get_fallback_reply(self, status):
        """Fallback reply when AI is not available."""
        scripts = self.config.get("scripts", {})
        fallbacks = {
            "new": scripts.get("opener", "Salut !"),
            "engaged": scripts.get("qualify_level", "Tu trades depuis combien de temps ?"),
            "qualified": scripts.get("trial", "On propose un essai 7 jours à 1€."),
            "book_call": scripts.get("handoff", "Je te mets en relation avec notre trader."),
            "follow_up": scripts.get("follow_up_1", "Toujours intéressé ?"),
            "not_qualified": scripts.get("close_lost", "Merci, bonne continuation !"),
            "closed_lost": scripts.get("close_lost", "Pas de souci, à bientôt !"),
        }
        return fallbacks.get(status, scripts.get("opener", "Salut !"))