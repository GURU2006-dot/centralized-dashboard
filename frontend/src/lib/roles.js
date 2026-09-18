export const ROLES = {
  ADMIN: "ADMIN",
  OFFICER: "ACQUISITION_OFFICER",
  APPROVER: "APPROVING_AUTHORITY",
  FIELD: "FIELD_OFFICER",
};

export const STAGES = [
  "SIA",
  "NOTIFICATION",
  "AWARD",
  "COMPENSATION_ASSESSMENT",
  "COMPENSATION_PAID",
  "POSSESSION",
  "REHABILITATION_RESETTLEMENT",
  "COMPLETED",
];

export function nextStage(current) {
  const i = STAGES.indexOf(current);
  if (i < 0 || i === STAGES.length - 1) return null;
  return STAGES[i + 1];
}

export function canWriteProjects(role) {
  return role === ROLES.ADMIN || role === ROLES.OFFICER;
}

export function canWriteProposals(role) {
  return role === ROLES.ADMIN || role === ROLES.OFFICER;
}

export function canApprove(role) {
  return role === ROLES.ADMIN || role === ROLES.APPROVER;
}

export function canTransition(role) {
  return role === ROLES.ADMIN || role === ROLES.OFFICER;
}

export function canField(role) {
  return role === ROLES.ADMIN || role === ROLES.FIELD;
}

export function canAudit(role) {
  return role === ROLES.ADMIN;
}

export function canReadProposals(role) {
  return role === ROLES.ADMIN || role === ROLES.OFFICER || role === ROLES.APPROVER;
}

export function canPredict(role) {
  return role === ROLES.ADMIN || role === ROLES.OFFICER || role === ROLES.APPROVER;
}

export const NAV = [
  {
    group: "Overview",
    items: [{ to: "/", label: "Dashboard", icon: "LayoutDashboard", roles: null }],
  },
  {
    group: "Land & Projects",
    items: [
      { to: "/projects", label: "Projects", icon: "Building2", roles: [ROLES.ADMIN, ROLES.OFFICER, ROLES.APPROVER] },
      { to: "/parcels", label: "Land Parcels", icon: "MapPinned", roles: null },
      { to: "/map", label: "GIS Map", icon: "Map", roles: null },
    ],
  },
  {
    group: "Acquisition",
    items: [
      { to: "/proposals", label: "Proposals", icon: "FileStack", roles: [ROLES.ADMIN, ROLES.OFFICER, ROLES.APPROVER] },
      { to: "/acquisitions", label: "Acquisition Cases", icon: "FolderKanban", roles: null },
      { to: "/workflow", label: "Workflow Tracker", icon: "GitBranch", roles: null },
    ],
  },
  {
    group: "Compensation & R&R",
    items: [
      { to: "/compensation", label: "Compensation", icon: "IndianRupee", roles: [ROLES.ADMIN, ROLES.OFFICER, ROLES.APPROVER] },
      { to: "/families", label: "Affected Families", icon: "Users", roles: [ROLES.ADMIN, ROLES.OFFICER, ROLES.APPROVER] },
      { to: "/rehabilitation", label: "Rehabilitation", icon: "HeartHandshake", roles: [ROLES.ADMIN, ROLES.OFFICER, ROLES.APPROVER] },
      { to: "/resettlement", label: "Resettlement", icon: "Home", roles: [ROLES.ADMIN, ROLES.OFFICER, ROLES.APPROVER] },
      { to: "/possession", label: "Possession", icon: "KeyRound", roles: [ROLES.ADMIN, ROLES.OFFICER, ROLES.APPROVER] },
    ],
  },
  {
    group: "Field Operations",
    items: [
      { to: "/field", label: "Field Verification", icon: "ClipboardCheck", roles: [ROLES.ADMIN, ROLES.FIELD] },
      { to: "/documents", label: "Documents", icon: "Files", roles: [ROLES.ADMIN, ROLES.OFFICER, ROLES.FIELD] },
    ],
  },
  {
    group: "Intelligence",
    items: [
      { to: "/analytics", label: "Analytics", icon: "ChartColumn", roles: [ROLES.ADMIN, ROLES.OFFICER, ROLES.APPROVER] },
      { to: "/model", label: "Model information", icon: "BrainCircuit", roles: [ROLES.ADMIN, ROLES.OFFICER, ROLES.APPROVER] },
      { to: "/reports", label: "Reports", icon: "FileBarChart", roles: [ROLES.ADMIN, ROLES.OFFICER, ROLES.APPROVER] },
      { to: "/alerts", label: "Alerts", icon: "Bell", roles: null },
    ],
  },
  {
    group: "System",
    items: [
      { to: "/notifications", label: "Notifications", icon: "Inbox", roles: null },
      { to: "/integrations", label: "Integrations", icon: "Cable", roles: [ROLES.ADMIN] },
      { to: "/audit", label: "Audit Logs", icon: "ScrollText", roles: [ROLES.ADMIN] },
      { to: "/users", label: "Users & Roles", icon: "Shield", roles: [ROLES.ADMIN] },
      { to: "/settings", label: "Settings", icon: "Settings", roles: null },
    ],
  },
];

export function visibleNav(role) {
  return NAV.map((g) => ({
    ...g,
    items: g.items.filter((item) => !item.roles || item.roles.includes(role)),
  })).filter((g) => g.items.length);
}
