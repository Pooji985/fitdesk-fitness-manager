# FitDesk Fitness Class & Membership Manager
## Project Specification & Architecture Document

---

### 1. Project Purpose & Overview
**FitDesk** is a modern, full-stack fitness management web application designed for gym owners, instructors, and members. The system streamlines gym operations by providing self-service booking, class schedule management, member profile tracking, and attendance verification. 

A standout feature is **weather-aware scheduling** for outdoor fitness classes (e.g., Bootcamps, Outdoor Yoga, Trail Runs) integrating with the **Open-Meteo API** to provide forecast insights and condition alerts before outdoor classes take place.

---

### 2. Agreed Technology Stack

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Frontend Framework** | **React** (via **Vite**) | Fast development feedback, modern component architecture, simple build tooling. |
| **Frontend Styling** | **Tailwind CSS** | Utility-first CSS for clean, responsive, and modern UI design. |
| **Backend Framework** | **Python 3.10+ / FastAPI** | High performance, automatic OpenAPI documentation, clean asynchronous support, type hints. |
| **Database** | **SQLite** (via SQLAlchemy / SQLModel) | Lightweight, serverless, zero-configuration file-based database ideal for student and prototype projects. |
| **Authentication** | **JWT (JSON Web Tokens)** | Stateless token-based authentication with role-based access control (RBAC). |
| **External Weather API** | **Open-Meteo API** | Free, open-access, no-API-key-required meteorological forecast API for outdoor class feasibility checks. |

---

### 3. User Roles & Permissions

1. **Admin / Manager**:
   - Manage all gym members (view, activate, deactivate, update membership tiers).
   - Create, edit, and cancel fitness classes and schedules.
   - Designate indoor vs. outdoor venues for classes.
   - View overall attendance records and booking reports.
2. **Trainer / Instructor**:
   - View assigned classes and enrolled attendees.
   - Mark/verify member attendance for their sessions.
   - Check weather warnings for upcoming outdoor classes.
3. **Member**:
   - Register, login, and manage personal profile.
   - Browse upcoming class schedules with filter options (indoor/outdoor, trainer, intensity).
   - Book class slots (subject to capacity and active membership).
   - View personal booking history and attendance status.
   - View weather condition indicators for outdoor classes.

---

### 4. Planned Core Features

#### Feature 1: Authentication & Role-Based Authorization
- User registration and login endpoints generating JWT access tokens.
- Secure password hashing using `passlib` / `bcrypt`.
- Role verification middleware/dependencies ensuring route protection (`admin`, `trainer`, `member`).

#### Feature 2: Member & Membership Tier Management
- Member profiles with contact info, emergency contacts, and active status.
- Membership tiers (e.g., Basic, Premium, Drop-in) dictating booking allowances.

#### Feature 3: Fitness Class & Schedule Management
- Class definitions: Title, description, trainer, capacity, duration, category (Strength, Yoga, Cardio, etc.).
- Location classification: **Indoor** vs. **Outdoor** with designated latitude/longitude or location coordinates.
- Recurring and one-off class timetables.

#### Feature 4: Weather-Aware Scheduling (Open-Meteo Integration)
- Outdoor class schedule cards query Open-Meteo for target time slots (temperature, precipitation probability, wind speed, weather condition codes).
- Status flags:
  - 🟢 **Optimal**: Mild temperature, no rain expected.
  - 🟡 **Warning**: Moderate rain risk, high heat, or high winds.
  - 🔴 **Inclement Weather / Action Needed**: Heavy rain or thunderstorm forecast — prompt staff to reschedule or move to indoor backup studio.
- Caching layer to avoid excessive weather requests.

#### Feature 5: Booking & Reservation Engine
- Real-time slot availability based on max capacity.
- Prevent double-booking for overlapping time slots.
- Cancellation and waitlist management.

#### Feature 6: Attendance Tracking
- Digital check-in system for instructors/trainers.
- Attendance statuses: `Booked`, `Attended`, `Cancelled`, `No-Show`.
- Historical attendance metrics for members and admins.

---

### 5. Project Directory Structure

```text
fitdesk-fitness-manager/
├── docs/
│   └── PROJECT_SPECIFICATION.md    # System specs, architecture, features
├── frontend/                       # React + Vite + Tailwind CSS client
│   ├── public/                     # Static assets
│   ├── src/
│   │   ├── assets/                 # Images, icons, static graphics
│   │   ├── components/             # Reusable UI components (buttons, modals, cards)
│   │   ├── context/                # React state context (Auth, Theme)
│   │   ├── pages/                  # Route-level views (Dashboard, Schedule, Classes)
│   │   └── services/               # API clients (axios / fetch helpers)
│   └── README.md                   # Frontend setup & scripts guide
├── backend/                        # FastAPI application
│   ├── app/
│   │   ├── api/                    # Route handlers (endpoints)
│   │   ├── core/                   # Security, JWT, configurations
│   │   ├── db/                     # SQLite connection, session management
│   │   ├── models/                 # SQLAlchemy / ORM database models
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   └── services/               # External services (Open-Meteo, business logic)
│   └── README.md                   # Backend setup & run guide
├── tests/                          # Automated tests
│   ├── backend/                    # Pytest test cases
│   ├── frontend/                   # Frontend component & unit tests
│   └── README.md                   # Test execution instructions
├── .gitignore                      # Git ignore patterns
└── README.md                       # Project overview
```

---

### 6. Implementation Milestones

1. **Phase 1: Project Setup & Foundation**
   - Initialize project skeletons, configs, and documentation *(Current Phase)*.
   - Configure SQLite database connection and migration setup.
2. **Phase 2: Authentication & Core Models**
   - Implement JWT authentication and user management in FastAPI.
   - Build login and registration UI in React.
3. **Phase 3: Class & Booking Management**
   - Class creation, timetable management, and booking endpoints.
   - Calendar / schedule interactive UI with capacity indicators.
4. **Phase 4: Weather Integration (Open-Meteo)**
   - Weather client service fetching forecast for outdoor venues.
   - Weather badge and alert components in the frontend.
5. **Phase 5: Attendance Tracking & Reporting**
   - Instructor attendance marking tools and member attendance logs.
6. **Phase 6: Testing, Polish & Delivery**
   - Backend unit and integration tests with pytest.
   - UI polish, responsive styling, and comprehensive user guides.
