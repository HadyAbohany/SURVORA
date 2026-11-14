from typing import Annotated, Any, Literal
from pydantic import BaseModel, Field, StringConstraints, AwareDatetime, field_validator, JsonValue

Language = Literal['en','ar']
Mode = Literal['TEXT_ONLY','VOICE_AND_TEXT','VISUAL_ALERT','SILENT']
Priority = Literal['low','normal','high','critical']

MissionId = Annotated[str, StringConstraints(max_length=80, pattern=r'^[A-Za-z0-9][A-Za-z0-9_-]*$')]
SessionId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
Percent = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]

class GameState(BaseModel):
    schema_version: str = '1.0'
    oxygen: Percent | None = None            # HUD percentage, not kg
    power: Percent | None = None             # HUD percentage, not kWh
    water: Percent | None = None
    food: Percent | None = None
    oxygen_generator_status: ShortText | None = None
    oxygen_trend: Annotated[float, Field(allow_inf_nan=False)] | None = None
    research_lab_on: bool | None = None
    rover_battery: Percent | None = None
    active_emergencies: list[ShortText] = Field(default_factory=list, max_length=16)
    buildings: dict[str, JsonValue] = Field(default_factory=dict)
    current_objective: ShortText | None = None
    current_stage: ShortText | None = None
    selected_sample_id: ShortText | None = None
    extra: dict[str, JsonValue] = Field(default_factory=dict)

    @field_validator('oxygen_generator_status', 'current_objective', 'current_stage',
                     'selected_sample_id', mode='before')
    @classmethod
    def blank_snapshot_field(cls, value):
        # Unity JsonUtility may encode an unset string as empty.
        return None if value == '' else value


class Evidence(BaseModel):
    source_id: str
    title: str
    url: str = ''
    provenance: str
    layer: Literal['nasa','game']
    mission_ids: tuple[str, ...] = ()
    document_version: str | None = None
    publication_date: str | None = None
    source_name: str | None = None
    source_modified_date: str | None = None
    excerpt: str = ''

class MissionRequest(BaseModel):
    mission_id: MissionId | None = None

    @field_validator('mission_id', mode='before')
    @classmethod
    def blank_mission(cls, value):
        return None if value == '' else value


class EventRequest(MissionRequest):
    schema_version: str = '1.0'
    event_id: str = Field(min_length=1, max_length=128)
    event_type: str = Field(min_length=2, max_length=100)
    priority: Priority = 'normal'
    session_id: SessionId = 'demo'
    language: Language = 'en'
    state_revision: int = Field(default=0, ge=0)
    timestamp: AwareDatetime | None = None
    game_state: GameState = Field(default_factory=GameState)

class EventReply(BaseModel):
    schema_version: str = '1.0'
    trigger_id: str
    should_speak: bool
    text: str
    response_mode: Mode
    priority: Priority
    voice_text: str = ''
    audio_ref: str | None = None
    sources: list[Evidence] = Field(default_factory=list)
    educational_explanation: str | None = None
    response_origin: str = 'predefined'
    followup_hint_recommended: bool = False
    state_revision: int = 0

class ChatRequest(MissionRequest):
    schema_version: str = '1.0'
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
    session_id: SessionId = 'demo'
    language: Language = 'en'
    age_mode: Literal['Explorer','Commander'] = 'Explorer'
    hint_level: int = Field(default=1, ge=0, le=3)
    game_state: GameState = Field(default_factory=GameState)
    allowed_actions: list[ShortText] = Field(default_factory=list, max_length=30)

class ModelDialogue(BaseModel, extra='forbid'):
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=650)]
    reference_ids: list[str] = Field(max_length=3)
    suggested_action: str | None


class ChatReply(BaseModel):
    answer: str
    suggested_action: str | None = None
    language: Language
    sources: list[Evidence] = Field(default_factory=list)
    grounding_status: str
    response_origin: str
    relevant_game_context: dict[str, Any]
    voice_text: str = ''
    audio_ref: str | None = None
    response_mode: Mode = 'TEXT_ONLY'

class AudioRequest(BaseModel):
    text: str = Field(min_length=1, max_length=400)
    language: Language = 'en'
