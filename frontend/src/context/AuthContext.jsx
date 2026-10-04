import React, { createContext, useContext, useEffect, useState } from 'react';
import { AUTH_TOKEN_STORAGE_KEY } from '../services/api';
import { authService } from '../services/authService';

export const ROLES = {
  ADMIN: 'admin',
  TRAINER: 'trainer',
  MEMBER: 'member',
};

export const USER_PROFILES = {
  [ROLES.ADMIN]: {
    id: 1,
    name: 'Alex Morgan',
    email: 'alex.morgan@fitdesk.io',
    role: ROLES.ADMIN,
    roleTitle: 'Gym Administrator',
    description: 'Full access to gym members, class schedules, and reports.',
    avatar: 'AM',
    badgeColor: 'bg-purple-500/10 text-purple-300 border-purple-500/30',
  },
  [ROLES.TRAINER]: {
    id: 2,
    name: 'Marcus Vance',
    email: 'marcus.trainer@fitdesk.io',
    role: ROLES.TRAINER,
    roleTitle: 'Senior Coach (HIIT & Outdoor)',
    description: 'Manages assigned classes, outdoor weather checks, and attendance.',
    avatar: 'MV',
    badgeColor: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30',
  },
  [ROLES.MEMBER]: {
    id: 3,
    name: 'Elena Rostova',
    email: 'elena.rostova@gmail.com',
    role: ROLES.MEMBER,
    roleTitle: 'Premium Member',
    membershipTier: 'Unlimited All-Access',
    description: 'Books fitness classes, checks weather warnings, and views attendance history.',
    avatar: 'ER',
    badgeColor: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
  },
};

const AuthContext = createContext();

function mapAuthenticatedUser(account) {
  const profile = USER_PROFILES[account.role] || USER_PROFILES[ROLES.MEMBER];
  return {
    ...profile,
    ...account,
    roleTitle: account.role_title || account.role,
    membershipTier: account.membership_tier,
    avatar: account.avatar || profile.avatar,
    description: 'Authenticated FitDesk account.',
  };
}

export function AuthProvider({ children }) {
  const [demoRole, setDemoRole] = useState(ROLES.ADMIN);
  const [authenticatedUser, setAuthenticatedUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);

    if (!token) {
      setAuthLoading(false);
      return () => { isMounted = false; };
    }

    authService.getCurrentUser()
      .then((account) => {
        if (isMounted) setAuthenticatedUser(mapAuthenticatedUser(account));
      })
      .catch(() => {
        localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
      })
      .finally(() => {
        if (isMounted) setAuthLoading(false);
      });

    return () => { isMounted = false; };
  }, []);

  const currentRole = authenticatedUser?.role || demoRole;
  const user = authenticatedUser || USER_PROFILES[demoRole];

  const switchRole = (newRole) => {
    if (!authenticatedUser && USER_PROFILES[newRole]) {
      setDemoRole(newRole);
    }
  };

  const establishSession = (session) => {
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, session.access_token);
    setAuthenticatedUser(mapAuthenticatedUser(session.user));
  };

  const login = async (credentials) => {
    const session = await authService.login(credentials);
    establishSession(session);
    return session.user;
  };

  const register = async (account) => {
    const session = await authService.register(account);
    establishSession(session);
    return session.user;
  };

  const logout = () => {
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    setAuthenticatedUser(null);
    setDemoRole(ROLES.ADMIN);
  };

  const isAdmin = currentRole === ROLES.ADMIN;
  const isTrainer = currentRole === ROLES.TRAINER;
  const isMember = currentRole === ROLES.MEMBER;

  return (
    <AuthContext.Provider
      value={{
        currentRole,
        user,
        switchRole,
        login,
        register,
        logout,
        isAuthenticated: Boolean(authenticatedUser),
        authLoading,
        ROLES,
        USER_PROFILES,
        isAdmin,
        isTrainer,
        isMember,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
