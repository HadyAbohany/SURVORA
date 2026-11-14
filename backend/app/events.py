"""Fast, deterministic event policy. Unity emits authoritative events and plays urgent local cues."""
from __future__ import annotations
from collections import OrderedDict
import time
from datetime import datetime, timezone
from threading import Lock
from .schemas import EventRequest,EventReply

# IDs deliberately align with the documented mission/events vocabulary.
MESSAGES={
 'MISSION_STARTED':('Mission started! Let’s find our first clue.','المهمة بدأت! يلا نبدأ بأول دليل.'),
 'MISSION_STAGE_COMPLETED':('Stage complete! Great progress.','خلصنا المرحلة! تقدم ممتاز.'),
 'MISSION_OBJECTIVE_UPDATED':('New objective! Check your mission panel.','عندنا هدف جديد! بص على لوحة المهمة.'),
 'MISSION_COMPLETED':('Mission complete! What did you discover?','المهمة نجحت! إيه اللي اكتشفته؟'),
 'MISSION_FAILED':('Good try! We can learn and try again.','محاولة كويسة! نتعلم ونجرب تاني.'),
 'NEW_AREA_DISCOVERED':('A new area! What clues can we find?','منطقة جديدة! يا ترى هنلاقي إيه؟'),
 'OXYGEN_LOW':('Oxygen is low. Check the oxygen plant and its power.','الأكسجين بيقل. اتأكد من محطة الأكسجين والكهرباء.'),
 'OXYGEN_RESTORED':('Great thinking! Oxygen production is stable again.','برافو! إنتاج الأكسجين رجع يستقر.'),
 'POWER_CRITICAL':('Power is critical. Prioritize life-support systems.','الطاقة قليلة جدًا. خلي الأولوية لأنظمة الحياة.'),
 'WATER_SHORTAGE':('Water is running low. Check the recycler.','الميه بتقل. راجع جهاز إعادة التدوير.'),
 'FOOD_SHORTAGE':('Food supplies are low. Check the greenhouse.','الأكل بيقل. راجع الصوبة.'),
 'BATTERY_DEPLETED':('Backup battery is empty. Check power generation.','البطارية الاحتياطية فضيت. راجع توليد الطاقة.'),
 'BUILDING_MALFUNCTION_CRITICAL':('A building needs attention. Open its status panel.','في مبنى محتاج صيانة. افتح حالته.'),
 'DUST_STORM_APPROACHING':('Dust storm ahead! Plan your power reserves.','عاصفة ترابية جاية! جهز احتياطي الطاقة.'),
 'DUST_STORM_STARTED':('Dust is reducing sunlight. Watch solar power.','التراب بيقلل ضوء الشمس. تابع الألواح.'),
 'DUST_STORM_ENDED':('The storm passed. Check dust on the panels.','العاصفة خلصت. راجع التراب على الألواح.'),
 'RADIATION_ALERT':('Radiation alert. Pause exploration and check shelter plans.','تنبيه إشعاع. وقف الاستكشاف وراجع خطة الاحتماء.'),
 'EXPLORATION_UNSAFE':('This area is unsafe right now. Review the map.','المنطقة دي مش آمنة دلوقتي. راجع الخريطة.'),
 'ROVER_BATTERY_LOW':('Rover battery is low. Plan a safe return.','بطارية الروفر قليلة. خطط للرجوع بأمان.'),
 'ROVER_DAMAGED':('The rover needs a repair. Check its status.','الروفر محتاج تصليح. راجع حالته.'),
 'SAMPLE_DISCOVERED':('A new sample! Try scanning it first.','عينة جديدة! جرب تعملها مسح الأول.'),
 'SAMPLE_SCANNED':('Nice scan! What can you observe?','مسح ممتاز! إيه اللي لاحظته؟'),
 'SAMPLE_ANALYZED':('Sample analyzed! Let’s explore what it means.','حللنا العينة! يلا نفهم معناها.'),
 'NEW_RESEARCH_UNLOCKED':('New research unlocked! Check the lab.','بحث جديد اتفتح! راجع المعمل.'),
 'PLAYER_STUCK':('Need a clue? Try checking the objective.','محتاج تلميح؟ راجع هدف المهمة.'),
 'REPEATED_FAILED_ACTION':('That did not work yet. Let’s try another idea.','لسه مش نافعة. خلينا نجرب فكرة تانية.'),
 'FIRST_SCIENCE_INTERACTION':('Science time! What do you think this system does?','وقت العلم! تفتكر النظام ده بيعمل إيه؟'),
 'EFFECTIVE_DECISION':('Smart choice! What changed after that?','قرار ذكي! إيه اللي اتغير بعده؟'),
 'MISSION_CHECKPOINT':('Checkpoint reached. What clue helped you get here?', 'وصلت لنقطة الحفظ. إيه الدليل اللي ساعدك؟'),
 'OBJECTIVE_RETRIED':('Try one change and watch what happens.', 'جرّب تغيّر حاجة واحدة وشوف إيه اللي يحصل.'),
 'OBJECTIVE_FAILED':('Which clue could you check before trying again?', 'إيه الدليل اللي ممكن تراجعه قبل ما تجرّب تاني؟'),
 'RESOURCE_CONSUMPTION_ABNORMAL':('A resource is dropping faster than usual in the game. What changed?', 'في مورد بيقل بسرعة أكتر من المعتاد في اللعبة. إيه اللي اتغير؟'),
 'POWER_LOW':('Power is running low. What is using it in your base?', 'الكهربا بتقل. إيه اللي بيستخدمها في القاعدة؟'),
 'PHENOMENON_DISCOVERED':('You spotted something new. What can you observe?', 'لاحظت حاجة جديدة. شايف إيه؟'),
 'NASA_ASSET_APPROACHED':('Take a closer look. What do you notice about this equipment?', 'بص عن قرب. إيه اللي لاحظته في الجهاز ده؟'),
 'CLUE_IGNORED':('Try looking at the clue again. What stands out?', 'بص على الدليل تاني. إيه اللي لفت نظرك؟'),
 'TECHNOLOGY_UNLOCKED':('New technology! Explore what it can improve.','تقنية جديدة! شوف ممكن تحسّن إيه.'),
}
URGENT={'OXYGEN_LOW','POWER_CRITICAL','BATTERY_DEPLETED','BUILDING_MALFUNCTION_CRITICAL','RADIATION_ALERT','EXPLORATION_UNSAFE'}
LOW_NOISE = {'MISSION_STAGE_COMPLETED', 'MISSION_OBJECTIVE_UPDATED', 'SAMPLE_SCANNED', 'EFFECTIVE_DECISION'}


class EventPolicy:
    def __init__(self, clock=time.monotonic, utcnow=lambda: datetime.now(timezone.utc)):
        self.clock = clock
        self.utcnow = utcnow
        self.seen = OrderedDict()
        self.last = OrderedDict()
        self.revisions = OrderedDict()
        self.lock = Lock()

    @staticmethod
    def _remember(cache, key, value, limit):
        cache[key] = value
        cache.move_to_end(key)
        if len(cache) > limit:
            cache.popitem(last=False)

    def handle(self, req: EventRequest):
        if req.event_type not in MESSAGES:
            return self._silent(req, 'unknown_event')
        if req.timestamp and not -30 <= (self.utcnow() - req.timestamp).total_seconds() <= 120:
            return self._silent(req, 'suppressed_timestamp')
        now = self.clock()
        with self.lock:
            while self.seen and now - next(iter(self.seen.values())) > 600:
                self.seen.popitem(last=False)
            idkey = (req.session_id, req.event_id)
            if idkey in self.seen:
                return self._silent(req, 'suppressed_duplicate')
            if req.state_revision:
                previous = self.revisions.get(req.session_id, 0)
                if req.state_revision < previous:
                    return self._silent(req, 'suppressed_stale_revision')
                self._remember(self.revisions, req.session_id, req.state_revision, 5000)
            self._remember(self.seen, idkey, now, 5000)
            urgent = req.priority == 'critical' or req.event_type in URGENT
            coolkey = (req.session_id, req.mission_id, req.event_type)
            if not urgent and now - self.last.get(coolkey, -1e10) < 30:
                return self._silent(req, 'suppressed_cooldown')
            if req.event_type in LOW_NOISE and req.priority == 'low':
                return self._silent(req, 'low_priority_suppressed')
            if not urgent:
                self._remember(self.last, coolkey, now, 5000)
        text=MESSAGES[req.event_type][0 if req.language=='en' else 1]
        if req.event_type=='MISSION_STARTED' and req.mission_id=='M02_OXYGEN_MYSTERY':
            text = ('Commander, welcome to Oxygen Mystery! Our oxygen plant needs a careful inspection. Ready to look for clues?' if req.language=='en' else 'أهلاً يا قائد في لغز الأكسجين! محطة الأكسجين محتاجة فحص. جاهز ندور على أدلة؟')
        return EventReply(trigger_id=req.event_id,should_speak=True,text=text,voice_text=text,response_mode='TEXT_ONLY',priority=('high' if urgent and req.priority in ('normal', 'low') else req.priority), response_origin='predefined',followup_hint_recommended=False,state_revision=req.state_revision)

    @staticmethod
    def _silent(req,why):
        return EventReply(trigger_id=req.event_id,should_speak=False,text='',response_mode='SILENT',priority=req.priority,response_origin=why,state_revision=req.state_revision)
