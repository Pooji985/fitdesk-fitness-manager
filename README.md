# FitDesk – Fitness Class & Membership Manager

FitDesk is a full-stack fitness management application designed to manage gym members, fitness classes, bookings, attendance, and outdoor class weather conditions.

The application is built with a React/Vite frontend and a FastAPI/SQLAlchemy backend using SQLite for local data storage. It includes JWT authentication and role-based access for Admin, Trainer, and Member users.

## Features

### Authentication & Role-Based Access

- JWT-based authentication
- Role-based access control
- Separate workflows for Admin, Trainer, and Member
- Secure password hashing
- Protected backend API endpoints

### Class & Schedule Management

- Create and manage fitness classes
- Indoor and outdoor class support
- Trainer assignment
- Class capacity management
- Class editing and cancellation
- Schedule filtering
- Upcoming class information

### Outdoor Weather Integration

- Open-Meteo weather integration for outdoor classes
- Weather information based on class location and time
- Weather status indicators
- Graceful handling when weather information is unavailable

### Bookings & Attendance

- Member class bookings
- Booking cancellation
- Capacity validation
- Attendance tracking
- Booking and attendance history
- Attendance statuses such as Booked, Attended, Cancelled, and No Show

### Member Management

- Admin member directory
- Member activation and deactivation
- Membership tier management
- Member profile management
- Emergency contact information

### Role-Based Dashboards

- Admin dashboard with gym-level metrics
- Trainer dashboard with assigned classes and attendance information
- Member dashboard with personal bookings and attendance
- Recent activity feed
- Live database metrics

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| ORM | SQLAlchemy |
| Database | SQLite |
| Authentication | JWT |
| Weather API | Open-Meteo |
| Testing | Python unittest |
| Version Control | Git, GitHub |

## Project Structure

```text
fitdesk-fitness-manager/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── pages/
│   │   └── services/
│   ├── package.json
│   └── vite.config.js
│
├── tests/
│   └── backend/
│
├── docs/
│   ├── PROJECT_SPECIFICATION.md
│   └── USER_GUIDE.md
│
├── .gitignore
├── README.md
└── ...