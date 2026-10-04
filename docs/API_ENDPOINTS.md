## API Endpoint List

### Authentication
| Method | Endpoint | Description | Access |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Register a new member | Public |
| POST | `/api/v1/auth/login` | User authentication and JWT token generation | Public |
| GET | `/api/v1/auth/me` | Get authenticated user information | Authenticated |

### Health
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/v1/health` | Check API and database connectivity | Public |

### Classes
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/v1/classes` | List and filter fitness classes | Authenticated |
| GET | `/api/v1/classes/trainers` | List available trainers | Authenticated |
| GET | `/api/v1/classes/{class_id}` | Get class details and weather | Authenticated |
| POST | `/api/v1/classes` | Create a fitness class | Admin |
| PATCH | `/api/v1/classes/{class_id}` | Update a fitness class | Admin |
| POST | `/api/v1/classes/{class_id}/cancel` | Cancel a fitness class | Admin |

### Bookings
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/v1/bookings` | View user's bookings | Authenticated |
| POST | `/api/v1/bookings` | Book a fitness class | Member |
| POST | `/api/v1/bookings/{booking_id}/cancel` | Cancel a booking | Member |

### Attendance
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/v1/attendance/classes/{class_id}` | View class attendance | Admin / Trainer |
| PATCH | `/api/v1/attendance/bookings/{booking_id}` | Update attendance status | Admin / Trainer |

### Members
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/v1/members` | List members | Admin |
| PATCH | `/api/v1/members/{member_id}` | Update member details/status/tier | Admin |
| GET | `/api/v1/members/me` | View own profile | Member |
| PATCH | `/api/v1/members/me` | Update own profile | Member |

### Dashboard
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/v1/dashboard/metrics` | Retrieve role-specific dashboard metrics | Authenticated |