# FitDesk User Guide

## Sign-In

Open the FitDesk frontend and use the Sign in panel. New registrations create Member accounts. Admin and Trainer demo credentials are provisioned locally; ask the project administrator for access. Passwords and JWT secrets are not stored in this guide.

## Admin

- **Dashboard:** View member, class, booking, attendance-status, and attendance-rate cards plus recent booking activity.
- **Members:** View member records; activate/deactivate accounts; update membership tier, phone, and emergency contact details.
- **Classes:** Create, edit, and cancel classes from Schedule. Class cancellation is a soft cancellation: existing bookings and attendance history remain stored and visible in booking history.
- **Attendance:** Select a class, review its enrolled members, and mark a booking Attended or No-Show.

## Trainer

- **Classes:** Browse the timetable and outdoor forecast indicators. Class creation, editing, and cancellation are Admin-only.
- **Attendance:** View rosters and mark attendance only for classes assigned to the signed-in Trainer.

## Member

- **Registration/Login:** Register as a Member or sign in with the account issued by the gym.
- **Profile:** View your own name/email and update phone and emergency contact details. Role, membership tier, and active status are managed by the gym.
- **Schedule:** Browse classes; filter by indoor/outdoor, trainer, category, search text, and optionally upcoming-only. Outdoor classes display weather status or a manual-check unavailable notice.
- **Booking:** Book a class while it has capacity, has not started, does not overlap another active booking, and your membership account is active. Cancel your own active booking from My Bookings.
- **History:** View your bookings and their Booked, Attended, No-Show, or Cancelled status. If a class itself is cancelled, its class-cancelled indicator is shown and its booking/attendance history is preserved.

## Scope Notes

These policies are not defined in the specification and are not implemented as inferred rules:

- Waitlist ordering, promotion, and member notification policy.
- Booking allowances or limits for each membership tier. The current booking gate checks active membership status and class availability.
- Recurring-class patterns, exceptions, and series-level editing/cancellation.
- Intensity levels and an intensity taxonomy/filter.

There is no payment, refund, email/SMS, or notification workflow. The frontend does not currently have an automated test runner; backend integration tests use Python `unittest` and must run against temporary database copies.
