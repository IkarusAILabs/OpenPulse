"""Evidence contract v1: standalone machine-consumable dependency evidence."""
from __future__ import annotations
import json,re
from pathlib import Path
from typing import Any
from core import attestation
from core.attestation import EvidenceContract
from core.evidence.provenance import hash_content
from core.schema.models import OSSEvent
CONTRACT_VERSION="1.0.0"
SCHEMA_PATH=Path(__file__).resolve().parents[1]/"schemas"/"evidence-contract"/"v1"/"schema.json"
_V1_RENAME={"contract_schema_version":"contract_version","event":"event_context","evidence_references":"evidence_refs","dates":"temporal"}
_V1_BODY_FIELDS=("contract_version","event_context","identity","scope","affected_dependency","assessment","evidence_refs","temporal","unknowns","recommendation","provenance")
def contract_version()->str:return CONTRACT_VERSION
def load_schema()->dict[str,Any]:return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
def build_v1_contract(event:OSSEvent,verdict:Any,finding:dict[str,Any]|None=None)->dict[str,Any]:
    doc=_rename_blocks(attestation.build_contract(event,verdict,finding));doc["contract_version"]=CONTRACT_VERSION;_set_content_hash(doc);return doc
def _rename_blocks(base:EvidenceContract)->dict[str,Any]:
    out={_V1_RENAME.get(k,k):v for k,v in base.model_dump(mode="json").items()};prov=out.get("provenance")
    if isinstance(prov,dict) and "contract_schema_version" in prov:prov.pop("contract_schema_version");prov["contract_version"]=CONTRACT_VERSION
    return out
def _hash_body(doc):
    body={n:doc[n] for n in _V1_BODY_FIELDS};body["provenance"]=dict(body["provenance"]);body["provenance"]["content_hash"]=attestation._HASH_PLACEHOLDER;body["provenance"]["generation_timestamp"]=attestation._TIMESTAMP_PLACEHOLDER;return hash_content(body)
def _set_content_hash(doc):doc["provenance"]["content_hash"]=_hash_body(doc)
def verify_v1_content_hash(doc):
    try:return _hash_body(doc)==doc["provenance"]["content_hash"]
    except (KeyError,TypeError):return False
_SUPPORTED=frozenset({"type","const","enum","anyOf","$ref","items","minItems","required","properties","additionalProperties","minLength","maxLength","pattern","format"})
_ANNOTATIONS=frozenset({"title","description","deprecated"})
def validate_v1_contract(doc,schema=None):
    schema=schema or load_schema();errors=[];_validate(doc,schema,schema,"$",errors);return errors
def _validation_errors(value,node,root,path):
    e=[];_validate(value,node,root,path,e);return e
def _validate(value,node,root,path,errors):
    for k in node:
        if k.startswith("$") or k in _ANNOTATIONS:continue
        if k not in _SUPPORTED:errors.append(f"{path}: schema uses unsupported keyword {k}")
    if "const" in node and not _eq(value,node["const"]):errors.append(f"{path}: expected const {node['const']!r}, got {value!r}")
    if "enum" in node and not any(_eq(value,x) for x in node["enum"]):errors.append(f"{path}: {value!r} is not one of {node['enum']}")
    if "anyOf" in node:
        if any(not _validation_errors(value,b,root,path) for b in node["anyOf"]):return
        errors.append(f"{path}: value {value!r} matches none of the anyOf branches");return
    if "$ref" in node:_validate(value,_resolve_ref(node["$ref"],root),root,path,errors);return
    typ=node.get("type")
    if typ is not None and not _type_ok(value,typ,path,errors):return
    if isinstance(value,str):
        if "minLength" in node and len(value)<node["minLength"]:errors.append(f"{path}: shorter than minLength")
        if "maxLength" in node and len(value)>node["maxLength"]:errors.append(f"{path}: longer than maxLength")
        if "pattern" in node and re.search(node["pattern"],value) is None:errors.append(f"{path}: pattern mismatch")
        fmt=node.get("format")
        if fmt=="date" and not _is_date(value):errors.append(f"{path}: invalid date")
        elif fmt=="date-time" and not _is_datetime(value):errors.append(f"{path}: invalid date-time")
        elif fmt=="uri" and not _is_uri(value):errors.append(f"{path}: invalid uri")
        elif fmt not in (None,"date","date-time","uri"):errors.append(f"{path}: unsupported format {fmt}")
    if isinstance(value,list):
        if "minItems" in node and len(value)<node["minItems"]:errors.append(f"{path}: fewer than minItems")
        if isinstance(node.get("items"),dict):
            for i,x in enumerate(value):_validate(x,node["items"],root,f"{path}[{i}]",errors)
    if isinstance(value,dict):
        for n in node.get("required",[]):
            if n not in value:errors.append(f"{path}: missing required property {n}")
        props=node.get("properties",{})
        if node.get("additionalProperties") is False:
            for n in value:
                if n not in props:errors.append(f"{path}: unexpected property {n}")
        for n,s in props.items():
            if n in value:_validate(value[n],s,root,f"{path}.{n}",errors)
def _resolve_ref(ref,root):
    if not ref.startswith("#/"):raise ValueError(f"unsupported ref {ref!r}")
    node=root
    for p in ref[2:].split("/"):node=node[p]
    return node
def _eq(a,b):
    if isinstance(a,bool) or isinstance(b,bool):return type(a)is type(b) and a==b
    return a==b
def _type_ok(value,typ,path,errors):
    ok={"object":isinstance(value,dict),"array":isinstance(value,list),"string":isinstance(value,str),"boolean":isinstance(value,bool),"null":value is None,"integer":isinstance(value,int) and not isinstance(value,bool),"number":isinstance(value,(int,float)) and not isinstance(value,bool)}.get(typ)
    if ok is None:errors.append(f"{path}: unsupported type {typ}");return False
    if not ok:errors.append(f"{path}: expected {typ}");return False
    return True
def _is_date(v):
    from datetime import date
    try:date.fromisoformat(v);return True
    except (ValueError,TypeError):return False
def _is_datetime(v):
    from datetime import datetime
    try:datetime.fromisoformat(v.replace("Z","+00:00"));return True
    except (ValueError,TypeError):return False
def _is_uri(v):return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:",v))
