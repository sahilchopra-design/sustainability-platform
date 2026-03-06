"""
Organisation management API — CRUD for multi-tenant organisations.

Admin-only for write operations; authenticated users can read their own org.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.base import get_db
from db.models.portfolio_pg import OrganisationPG, OrgUserPG, UserPG
from api.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/v1/organisations", tags=["organisations"])


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class OrgCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    short_name: Optional[str] = Field(None, max_length=100)
    org_type: str = Field("financial_institution", max_length=50)
    jurisdiction: Optional[str] = Field(None, max_length=3)
    regulatory_regime: Optional[str] = None
    subscription_tier: str = Field("professional")


class OrgUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=500)
    short_name: Optional[str] = Field(None, max_length=100)
    org_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    regulatory_regime: Optional[str] = None
    subscription_tier: Optional[str] = None
    is_active: Optional[bool] = None


class OrgUserCreate(BaseModel):
    email: str = Field(..., min_length=3)
    full_name: Optional[str] = None
    role: str = Field("analyst")
    department: Optional[str] = None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _org_to_dict(org: OrganisationPG) -> dict:
    return {
        "id": str(org.id),
        "name": org.name,
        "short_name": org.short_name,
        "org_type": org.org_type,
        "jurisdiction": org.jurisdiction,
        "regulatory_regime": org.regulatory_regime,
        "subscription_tier": org.subscription_tier,
        "lei": org.lei,
        "is_active": org.is_active,
        "created_at": org.created_at.isoformat() if org.created_at else None,
    }


# ── List / Get ───────────────────────────────────────────────────────────────

@router.get("/", summary="List all organisations")
def list_organisations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    orgs = db.query(OrganisationPG).order_by(OrganisationPG.name).offset(offset).limit(limit).all()
    total = db.query(OrganisationPG).count()
    return {"total": total, "organisations": [_org_to_dict(o) for o in orgs]}


@router.get("/mine", summary="Get current user's organisation")
def get_my_org(
    db: Session = Depends(get_db),
    user: UserPG = Depends(get_current_user),
):
    org_id = getattr(user, "org_id", None)
    if not org_id:
        return {"organisation": None, "message": "No organisation assigned"}
    org = db.get(OrganisationPG, org_id)
    if not org:
        return {"organisation": None, "message": "Organisation not found"}
    # Count org members
    member_count = db.query(OrgUserPG).filter(OrgUserPG.org_id == org_id).count()
    result = _org_to_dict(org)
    result["member_count"] = member_count
    return {"organisation": result}


@router.get("/{org_id}", summary="Get organisation by ID")
def get_organisation(
    org_id: UUID,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    org = db.get(OrganisationPG, org_id)
    if not org:
        raise HTTPException(404, "Organisation not found")
    member_count = db.query(OrgUserPG).filter(OrgUserPG.org_id == org_id).count()
    result = _org_to_dict(org)
    result["member_count"] = member_count
    return result


# ── Create / Update ──────────────────────────────────────────────────────────

@router.post("/", summary="Create a new organisation", status_code=201)
def create_organisation(
    body: OrgCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    org = OrganisationPG(
        name=body.name,
        short_name=body.short_name,
        org_type=body.org_type,
        jurisdiction=body.jurisdiction,
        regulatory_regime=body.regulatory_regime,
        subscription_tier=body.subscription_tier,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return _org_to_dict(org)


@router.put("/{org_id}", summary="Update an organisation")
def update_organisation(
    org_id: UUID,
    body: OrgUpdate,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    org = db.get(OrganisationPG, org_id)
    if not org:
        raise HTTPException(404, "Organisation not found")
    for field, val in body.dict(exclude_unset=True).items():
        setattr(org, field, val)
    db.commit()
    db.refresh(org)
    return _org_to_dict(org)


# ── Org Members ──────────────────────────────────────────────────────────────

@router.get("/{org_id}/members", summary="List members of an organisation")
def list_org_members(
    org_id: UUID,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    members = db.query(OrgUserPG).filter(OrgUserPG.org_id == org_id).order_by(OrgUserPG.full_name).all()
    return {
        "org_id": str(org_id),
        "members": [
            {
                "id": str(m.id),
                "email": m.email,
                "full_name": m.full_name,
                "role": m.role,
                "department": m.department,
                "is_active": m.is_active,
                "last_login": m.last_login.isoformat() if m.last_login else None,
            }
            for m in members
        ],
    }


@router.post("/{org_id}/members", summary="Add a member to an organisation", status_code=201)
def add_org_member(
    org_id: UUID,
    body: OrgUserCreate,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    org = db.get(OrganisationPG, org_id)
    if not org:
        raise HTTPException(404, "Organisation not found")
    # Check duplicate
    existing = db.query(OrgUserPG).filter(
        OrgUserPG.org_id == org_id, OrgUserPG.email == body.email
    ).first()
    if existing:
        raise HTTPException(400, "User already a member of this organisation")
    member = OrgUserPG(
        org_id=org_id,
        email=body.email,
        full_name=body.full_name,
        role=body.role,
        department=body.department,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return {
        "id": str(member.id),
        "org_id": str(org_id),
        "email": member.email,
        "role": member.role,
    }
