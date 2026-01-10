from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db.models import Sum, Count, Max
from django.http import HttpResponse

from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib.units import inch

from apps.accounts.models import User
from apps.financial.models import FinancialAccount, Deposit


class AdminAnalyticsViewSet(GenericViewSet):
    """
    Admin Analytics ViewSet
    URLs:
    /api/admin/analytics/members/
    /api/admin/analytics/summary/
    /api/admin/analytics/export/?format=excel|pdf
    """

    permission_classes = [IsAuthenticated]

    def _check_admin(self, request):
        if request.user.role != "admin":
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    # ------------------------------------------------------------------
    # MEMBERS ANALYTICS
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"])
    def members(self, request):
        admin_check = self._check_admin(request)
        if admin_check:
            return admin_check

        users = User.objects.filter(role="user").select_related("financial_account")

        total_all_contributions = (
            FinancialAccount.objects.aggregate(
                total=Sum("total_contributions")
            )["total"]
            or Decimal("0")
        )

        member_analytics = []

        for user in users:
            account, _ = FinancialAccount.objects.get_or_create(user=user)

            deposit_stats = Deposit.objects.filter(
                user=user, status="completed"
            ).aggregate(
                total_deposits=Count("id"),
                last_deposit=Max("created_at"),
            )

            contribution_percentage = (
                float(account.total_contributions / total_all_contributions * 100)
                if total_all_contributions > 0
                else 0
            )

            member_analytics.append(
                {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "total_contributions": float(account.total_contributions),
                    "total_deposits": deposit_stats["total_deposits"],
                    "interest_earned": float(account.interest_earned),
                    "activity_status": user.activity_status,
                    "created_at": user.created_at.isoformat(),
                    "last_deposit_date": deposit_stats["last_deposit"].isoformat()
                    if deposit_stats["last_deposit"]
                    else None,
                    "contribution_percentage": round(contribution_percentage, 2),
                }
            )

        summary = {
            "total_contributions": float(total_all_contributions),
            "total_members": users.count(),
            "active_members": users.filter(activity_status="Active").count(),
            "average_contribution": float(
                total_all_contributions / users.count()
            )
            if users.exists()
            else 0,
            "total_deposits_count": Deposit.objects.filter(
                status="completed"
            ).count(),
            "total_interest_earned": float(
                FinancialAccount.objects.aggregate(
                    total=Sum("interest_earned")
                )["total"]
                or Decimal("0")
            ),
        }

        monthly_trends = []
        for i in range(11, -1, -1):
            month_start = datetime.now().replace(day=1) - timedelta(days=30 * i)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            month_data = Deposit.objects.filter(
                status="completed",
                created_at__gte=month_start,
                created_at__lte=month_end,
            ).aggregate(
                total_amount=Sum("amount"),
                deposit_count=Count("id"),
            )

            monthly_trends.append(
                {
                    "month": month_start.strftime("%b"),
                    "year": month_start.year,
                    "total_amount": float(month_data["total_amount"] or 0),
                    "deposit_count": month_data["deposit_count"],
                }
            )

        return Response(
            {
                "members": member_analytics,
                "summary": summary,
                "monthly_trends": monthly_trends,
            }
        )

    # ------------------------------------------------------------------
    # SUMMARY ONLY
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"])
    def summary(self, request):
        admin_check = self._check_admin(request)
        if admin_check:
            return admin_check

        users = User.objects.filter(role="user")

        total_contributions = (
            FinancialAccount.objects.aggregate(
                total=Sum("total_contributions")
            )["total"]
            or Decimal("0")
        )

        return Response(
            {
                "total_contributions": float(total_contributions),
                "total_members": users.count(),
                "active_members": users.filter(activity_status="Active").count(),
                "average_contribution": float(
                    total_contributions / users.count()
                )
                if users.exists()
                else 0,
                "total_deposits_count": Deposit.objects.filter(
                    status="completed"
                ).count(),
                "total_interest_earned": float(
                    FinancialAccount.objects.aggregate(
                        total=Sum("interest_earned")
                    )["total"]
                    or Decimal("0")
                ),
            }
        )

    # ------------------------------------------------------------------
    # EXPORT
    # ------------------------------------------------------------------
    @action(detail=False, methods=["get"],url_path="export",url_name="export")
    def export_analytics(self, request):
        admin_check = self._check_admin(request)
        if admin_check:
            return admin_check

        export_format = request.query_params.get("format", "excel")

        if export_format not in ("excel", "pdf"):
            return Response(
                {"error": 'Invalid format. Use "excel" or "pdf".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        users = User.objects.filter(role="user").select_related("financial_account")

        member_data = []
        for user in users:
            account, _ = FinancialAccount.objects.get_or_create(user=user)
            member_data.append(
                {
                    "name": user.full_name,
                    "email": user.email,
                    "contributions": float(account.total_contributions),
                    "deposits": Deposit.objects.filter(
                        user=user, status="completed"
                    ).count(),
                    "interest": float(account.interest_earned),
                    "status": user.activity_status,
                }
            )

        return (
            self._export_excel(member_data)
            if export_format == "excel"
            else self._export_pdf(member_data)
        )

    # ------------------------------------------------------------------
    # EXCEL EXPORT
    # ------------------------------------------------------------------
    def _export_excel(self, member_data):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Member Analytics"

        header_fill = PatternFill("solid", fgColor="3B82F6")
        header_font = Font(color="FFFFFF", bold=True)

        headers = [
            "Name",
            "Email",
            "Total Contributions",
            "Deposits",
            "Interest Earned",
            "Status",
        ]

        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        for row, member in enumerate(member_data, start=2):
            ws.append(
                [
                    member["name"],
                    member["email"],
                    f"KES {member['contributions']:,.2f}",
                    member["deposits"],
                    f"KES {member['interest']:,.2f}",
                    member["status"],
                ]
            )

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response[
            "Content-Disposition"
        ] = f'attachment; filename="member-analytics-{datetime.now():%Y%m%d}.xlsx"'
        return response

    # ------------------------------------------------------------------
    # PDF EXPORT
    # ------------------------------------------------------------------
    def _export_pdf(self, member_data):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Member Analytics Report", styles["Title"]))
        elements.append(Spacer(1, 0.3 * inch))

        table_data = [
            ["Name", "Email", "Contributions", "Deposits", "Interest", "Status"]
        ]

        for m in member_data:
            table_data.append(
                [
                    m["name"],
                    m["email"],
                    f"KES {m['contributions']:,.2f}",
                    m["deposits"],
                    f"KES {m['interest']:,.2f}",
                    m["status"],
                ]
            )

        table = Table(table_data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3B82F6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        elements.append(table)
        doc.build(elements)

        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type="application/pdf")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="member-analytics-{datetime.now():%Y%m%d}.pdf"'
        return response
