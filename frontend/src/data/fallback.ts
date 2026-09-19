import {
  activityEvents,
  cameras,
  facilityInfo,
  incidents,
  procedures,
  recommendedActions,
  systemServices,
} from "@/data/mock";
import type {
  ActivityEvent,
  Camera,
  FacilityInfo,
  Incident,
  RecommendedAction,
  SafetyProcedure,
  SystemService,
} from "@/types";

export function getFallbackFacility(): FacilityInfo {
  return facilityInfo;
}

export function getFallbackCameras(): Camera[] {
  return cameras;
}

export function getFallbackIncidents(): Incident[] {
  return incidents;
}

export function getFallbackActiveIncident(): Incident {
  return incidents[0];
}

export function getFallbackActivity(): ActivityEvent[] {
  return activityEvents;
}

export function getFallbackServices(): SystemService[] {
  return systemServices;
}

export function getFallbackProcedures(): SafetyProcedure[] {
  return procedures;
}

export function getFallbackActions(): RecommendedAction[] {
  return recommendedActions;
}

export function getFallbackIncidentDetail() {
  const incident = incidents[0];
  return {
    incident,
    camera: cameras.find((item) => item.id === incident.cameraId) ?? cameras[0],
    actions: recommendedActions,
    procedure: procedures[0],
    evidenceDescriptions: [incident.evidence],
  };
}
