"""
Fare Checker: compares a logged trip against the reference commission rate.

A trip is FLAGGED when either:
  1. the commission deducted is higher than the reference rate allows, or
  2. the net amount received is lower than gross - deductions + tips
     (money went missing between the breakdown and the payout).

Small differences are ignored: the tolerance is ₱1.00 or 1% of the gross fare,
whichever is larger, so rounding by the platform does not cause false flags.
"""

from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone

CENT = Decimal("0.01")
MIN_TOLERANCE = Decimal("1.00")
TOLERANCE_PERCENT = Decimal("1")


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def tolerance_for(gross_fare):
    return max(MIN_TOLERANCE, money(gross_fare * TOLERANCE_PERCENT / 100))


def find_rate(platform, service_type, on_date):
    """The reference rate that applied to this platform/service on the trip date."""
    from .models import CommissionRate

    return (
        CommissionRate.objects.filter(
            platform=platform, service_type=service_type, effective_from__lte=on_date
        )
        .order_by("-effective_from")
        .first()
    )


def run_fare_check(trip):
    """Fill in the trip's fare-check fields. Does not save the trip."""
    from .models import Trip

    gross = money(trip.gross_fare)
    commission = money(trip.commission_deducted)
    other = money(trip.other_deductions or 0)
    tips = money(trip.tips or 0)
    net = money(trip.net_received)
    tolerance = tolerance_for(gross)
    reasons = []

    rate = find_rate(trip.platform_id, trip.service_type, trip.trip_date) if trip.platform_id else None
    trip.applied_rate = rate

    if rate is not None:
        expected = money(gross * rate.commission_percent / 100)
        overcharge = commission - expected
        trip.expected_commission = expected
        trip.commission_overcharge = overcharge
        if overcharge > tolerance:
            reasons.append(
                f"Commission was ₱{overcharge:,.2f} more than expected: the {rate.platform} "
                f"reference rate is {rate.commission_percent}% (₱{expected:,.2f}), "
                f"but ₱{commission:,.2f} was deducted."
            )
    else:
        trip.expected_commission = None
        trip.commission_overcharge = None

    expected_net = gross - commission - other + tips
    shortfall = expected_net - net
    trip.net_shortfall = shortfall if shortfall > 0 else Decimal("0.00")
    if shortfall > tolerance:
        reasons.append(
            f"You received ₱{shortfall:,.2f} less than your breakdown adds up to "
            f"(₱{gross:,.2f} gross - ₱{commission + other:,.2f} deductions + ₱{tips:,.2f} tips "
            f"= ₱{expected_net:,.2f}, but only ₱{net:,.2f} was received)."
        )

    if reasons:
        trip.check_status = Trip.CheckStatus.FLAGGED
    elif rate is None:
        trip.check_status = Trip.CheckStatus.NO_RATE
    else:
        trip.check_status = Trip.CheckStatus.OK
    trip.flag_reasons = "\n".join(reasons)
    trip.checked_at = timezone.now()
    return trip


def recheck_trips(platform, service_type):
    """Re-run the check for every trip a rate change could affect. Returns the count."""
    from .models import Trip

    trips = Trip.objects.filter(platform=platform, service_type=service_type)
    count = 0
    for trip in trips.iterator():
        trip.save()
        count += 1
    return count
