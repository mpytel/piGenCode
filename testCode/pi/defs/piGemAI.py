from pi.defs.logIt import printIt, lable, cStr, color
from pi.commands.commands import Commands
from google import genai
from google.genai import types
import os

API_KEY = os.environ.get("GOOGLE_API_KEY")

sys_instruct="You are a linguistic expert. When a single word in entered you will return approiate values in this json structure for that word:\n"
sys_instruct+= ' \
  "piBody": {\
    "LexicalMeaning": "",\
    "SemanticRoles": "",\
    "PartOfSpeech": "",\
    "ConnotationAndDenotation": "",\
    "SinglerOrPlural": "",\
    "RegisterAndStyle": "",\
    "Pronunciation": "",\
    "FrequencyAndUsage": 0\
  }\
'

def piGemAI(prompt):
    client = genai.Client(api_key="GEMINI_API_KEY")

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=sys_instruct),
        contents=[prompt]
    )
'''
    http_options: HttpOptions | None = None,
    system_instruction: ContentUnion | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: float | None = None,
    candidate_count: int | None = None,
    max_output_tokens: int | None = None,
    stop_sequences: list[str] | None = None,
    response_logprobs: bool | None = None,
    logprobs: int | None = None,
    presence_penalty: float | None = None,
    frequency_penalty: float | None = None,
    seed: int | None = None,
    response_mime_type: str | None = None,
    response_schema: SchemaUnion | None = None,
    routing_config: GenerationConfigRoutingConfig | None = None,
    safety_settings: list[SafetySetting] | None = None,
    tools: ToolListUnion | None = None,
    tool_config: ToolConfig | None = None,
    labels: dict[str, str] | None = None,
    cached_content: str | None = None,
    response_modalities: list[str] | None = None,
    media_resolution: MediaResolution | None = None,
    speech_config: SpeechConfigUnion | None = None,
    audio_timestamp: bool | None = None,
    automatic_function_calling: AutomaticFunctionCallingConfig | None = None,
    thinking_config: ThinkingConfig | None = None

types.GenerateContentConfig
__abstractmethods__
__annotations__
__class__
__class_getitem__
__class_vars__
__copy__
__deepcopy__
__delattr__
__dict__
__dir__
__doc__
__eq__
__fields__
__fields_set__
__format__
__ge__
__get_pydantic_core_schema__
__get_pydantic_json_schema__
__getattr__
__getattribute__
__getstate__
__gt__
__hash__
__init__
__init_subclass__
__iter__
__le__
__lt__
__module__
__ne__
__new__
__pretty__
__private_attributes__
__pydantic_complete__
__pydantic_core_schema__
__pydantic_custom_init__
__pydantic_decorators__
__pydantic_extra__
__pydantic_fields_set__
__pydantic_generic_metadata__
__pydantic_init_subclass__
__pydantic_parent_namespace__
__pydantic_post_init__
__pydantic_private__
__pydantic_root_model__
__pydantic_serializer__
__pydantic_validator__
__reduce__
__reduce_ex__
__repr__
__repr_args__
__repr_name__
__repr_str__
__rich_repr__
__setattr__
__setstate__
__signature__
__sizeof__
__slots__
__str__
__subclasshook__
__weakref__
_abc_impl
_calculate_keys
_convert_literal_to_enum
_copy_and_set_values
_from_response
_get_value
_iter
construct
copy
dict
from_orm
json
model_computed_fields
model_config
model_construct
model_copy
model_dump
model_dump_json
model_extra
model_fields
model_fields_set
model_json_schema
model_parametrized_name
model_post_init
model_rebuild
model_validate
model_validate_json
model_validate_strings
parse_file
parse_obj
parse_raw
schema
schema_json
to_json_dict
update_forward_refs
validate

'''
