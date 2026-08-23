def calculate_payment_recovery(summary):
    invoice_total = float(summary["invoice_total"])
    payment_total = float(summary["payment_total"])

    if invoice_total == 0:
        return 0.0

    return (payment_total / invoice_total) * 100


def calculate_difference(summary_a, summary_b):
    return {
        "orders": summary_a["orders"] - summary_b["orders"],
        "invoice_total": (
            summary_a["invoice_total"]
            - summary_b["invoice_total"]
        ),
        "payment_total": (
            summary_a["payment_total"]
            - summary_b["payment_total"]
        ),
        "outstanding": (
            summary_a["outstanding"]
            - summary_b["outstanding"]
        ),
        "cancelled_orders": (
            summary_a["cancelled_orders"]
            - summary_b["cancelled_orders"]
        ),
        "pending_orders": (
            summary_a["pending_orders"]
            - summary_b["pending_orders"]
        ),
        "processing_orders": (
            summary_a["processing_orders"]
            - summary_b["processing_orders"]
        ),
    }


def format_comparison(summary_a, summary_b):
    difference = calculate_difference(summary_a, summary_b)

    return (
        f"**{summary_a['customer']} vs {summary_b['customer']}**\n\n"
        f"- Orders: {summary_a['orders']} vs "
        f"{summary_b['orders']} "
        f"(difference: {abs(difference['orders'])})\n"
        f"- Invoice Total: ₹{summary_a['invoice_total']:,} vs "
        f"₹{summary_b['invoice_total']:,}\n"
        f"- Payment Total: ₹{summary_a['payment_total']:,} vs "
        f"₹{summary_b['payment_total']:,}\n"
        f"- Outstanding: ₹{summary_a['outstanding']:,} vs "
        f"₹{summary_b['outstanding']:,}"
    )


def format_payment_recovery(summary_a, summary_b):
    recovery_a = calculate_payment_recovery(summary_a)
    recovery_b = calculate_payment_recovery(summary_b)

    if recovery_a > recovery_b:
        better = summary_a["customer"]
    else:
        better = summary_b["customer"]

    return (
        "Payment recovery:\n\n"
        f"- {summary_a['customer']}: "
        f"{recovery_a:.2f}%\n"
        f"- {summary_b['customer']}: "
        f"{recovery_b:.2f}%\n\n"
        f"{better} has the higher payment recovery rate."
    )


def format_customer_summary(summary):
    return (
        f"**{summary['customer']} Summary**\n\n"
        f"- Total Orders: {summary['orders']}\n"
        f"- Cancelled Orders: {summary['cancelled_orders']}\n"
        f"- Pending Orders: {summary['pending_orders']}\n"
        f"- Processing Orders: {summary['processing_orders']}\n"
        f"- Invoice Total: ₹{summary['invoice_total']:,}\n"
        f"- Payment Total: ₹{summary['payment_total']:,}\n"
        f"- Outstanding: ₹{summary['outstanding']:,}"
    )