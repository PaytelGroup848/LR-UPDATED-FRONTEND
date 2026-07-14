"use client";

import { useCallback, useEffect, useState } from "react";
import type { Agent, Application, Monitoring, Server, Session, SessionStats, User } from "@/types/admin";
import { getApplications, getServers } from "@/services/application.service";
import { getAgents, getMonitoring } from "@/services/monitoring.service";
import { getSessions, getSessionStats } from "@/services/session.service";
import { getUsers } from "@/services/user.service";

export function useAdminData() {
  const [users, setUsers] = useState<User[]>([]);
  const [servers, setServers] = useState<Server[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [stats, setStats] = useState<SessionStats>({});
  const [agents, setAgents] = useState<Agent[]>([]);
  const [monitoring, setMonitoring] = useState<Monitoring>({});
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);

    const [nextUsers, nextServers, nextApplications, nextSessions, nextStats, nextAgents, nextMonitoring] =
      await Promise.all([
        getUsers(),
        getServers(),
        getApplications(),
        getSessions(),
        getSessionStats(),
        getAgents(),
        getMonitoring()
      ]);

    setUsers(nextUsers);
    setServers(nextServers);
    setApplications(nextApplications);
    setSessions(nextSessions);
    setStats(nextStats);
    setAgents(nextAgents);
    setMonitoring(nextMonitoring);
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    users,
    servers,
    applications,
    sessions,
    stats,
    agents,
    monitoring,
    loading,
    refresh
  };
}
