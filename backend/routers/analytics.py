from fastapi import APIRouter
from typing import Dict

router = APIRouter()


@router.get("/overview")
def overview():
    # Static data matching frontend mock for easy integration
    qcStatusData = [
        {"name": "PASS", "value": 217, "color": "#22c55e"},
        {"name": "FIX", "value": 20, "color": "#eab308"},
        {"name": "FLAG", "value": 11, "color": "#ef4444"},
    ]

    deviceData = [
        {"device": "GE Discovery", "pass": 95, "fix": 8, "flag": 3},
        {"device": "Siemens Multix", "pass": 72, "fix": 7, "flag": 5},
        {"device": "Philips Digital", "pass": 50, "fix": 5, "flag": 3},
    ]

    trendData = [
        {"month": "Jul", "passRate": 85},
        {"month": "Aug", "passRate": 86},
        {"month": "Sep", "passRate": 84},
        {"month": "Oct", "passRate": 88},
        {"month": "Nov", "passRate": 87.5},
    ]

    stats = [
        {"label": "Pass Rate", "value": "87.5%", "change": "+2.1%", "trend": "up"},
        {"label": "Flag Rate", "value": "4.4%", "change": "-0.8%", "trend": "down"},
        {"label": "Avg. Processing Time", "value": "2.3 min", "change": "-0.4 min", "trend": "down"},
        {"label": "Total Scans", "value": "248", "change": "+12", "trend": "up"},
    ]

    top_issues = [
        {"issue": "Rotation > 5°", "count": 15, "percentage": 60},
        {"issue": "Poor Coverage", "count": 8, "percentage": 32},
        {"issue": "Motion Blur", "count": 5, "percentage": 20},
        {"issue": "Overexposure", "count": 3, "percentage": 12},
    ]

    return {
        "qcStatusData": qcStatusData,
        "deviceData": deviceData,
        "trendData": trendData,
        "stats": stats,
        "top_issues": top_issues,
    }
