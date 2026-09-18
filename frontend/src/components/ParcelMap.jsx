import { useEffect, useMemo, useState } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

function Fit({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [24, 24], maxZoom: 16 });
  }, [bounds, map]);
  return null;
}

function featureColor(feat, mode) {
  const p = feat.properties || {};
  if (mode === "risk") {
    if (p.risk_level === "HIGH") return "#be123c";
    if (p.risk_level === "MEDIUM") return "#b45309";
    if (p.risk_level === "LOW") return "#0f766e";
    return "#94a3b8";
  }
  if (mode === "stage") {
    const map = {
      SIA: "#1d4ed8",
      NOTIFICATION: "#0369a1",
      AWARD: "#7c3aed",
      COMPENSATION_ASSESSMENT: "#b45309",
      COMPENSATION_PAID: "#0f766e",
      POSSESSION: "#115e59",
      REHABILITATION_RESETTLEMENT: "#6d28d9",
      COMPLETED: "#365314",
    };
    return map[p.current_stage] || "#475569";
  }
  switch (p.acquisition_status) {
    case "ACQUIRED":
      return "#0f766e";
    case "IN_PROCESS":
      return "#b45309";
    case "NOTIFIED":
      return "#1d4ed8";
    default:
      return "#475569";
  }
}

export default function ParcelMap({
  features,
  onSelect,
  height = "28rem",
  colorMode = "status",
  onTileError,
  onSwitchToTable,
}) {
  const [tileError, setTileError] = useState(false);
  const [tileKey, setTileKey] = useState(0);

  const collection = useMemo(() => {
    const list = (features || []).filter((f) => f?.geometry);
    return { type: "FeatureCollection", features: list };
  }, [features]);

  const bounds = useMemo(() => {
    if (!collection.features.length) return null;
    try {
      return L.geoJSON(collection).getBounds();
    } catch {
      return null;
    }
  }, [collection]);

  const center = bounds?.isValid() ? bounds.getCenter() : { lat: 17.385, lng: 78.486 };

  const handleTileError = () => {
    setTileError(true);
    if (onTileError) {
      onTileError(true);
    }
  };

  const handleRetryTiles = () => {
    setTileError(false);
    setTileKey((k) => k + 1);
  };

  return (
    <div
      className="relative overflow-hidden rounded-2xl border border-line bg-slate-100"
      style={{ height }}
      data-testid="parcel-map-container"
    >
      {tileError ? (
        <div
          role="alert"
          aria-live="polite"
          className="absolute top-3 left-3 right-3 z-[1000] flex flex-wrap items-center justify-between gap-2 rounded-xl border border-amber-300 bg-amber-50/95 px-3.5 py-2.5 text-xs text-amber-900 shadow-md backdrop-blur-sm"
        >
          <div className="flex items-center gap-2">
            <span className="inline-block h-2.5 w-2.5 shrink-0 rounded-full bg-amber-500 animate-pulse" />
            <span>
              <strong className="font-semibold">Basemap unavailable:</strong> OpenStreetMap tiles could not be loaded. Parcel spatial data and vector boundaries remain fully available.
            </span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {onSwitchToTable ? (
              <button
                type="button"
                onClick={onSwitchToTable}
                className="rounded px-2 py-0.5 font-medium text-navy hover:bg-amber-100 underline cursor-pointer"
              >
                View parcel table
              </button>
            ) : null}
            <button
              type="button"
              onClick={handleRetryTiles}
              className="rounded px-2 py-0.5 font-medium text-amber-900 hover:bg-amber-100 underline cursor-pointer"
            >
              Retry basemap
            </button>
            <button
              type="button"
              onClick={() => setTileError(false)}
              className="rounded px-1.5 py-0.5 text-amber-700 hover:bg-amber-100 hover:text-amber-900 cursor-pointer"
              title="Dismiss warning"
              aria-label="Dismiss tile failure notification"
            >
              ✕
            </button>
          </div>
        </div>
      ) : null}

      <MapContainer center={[center.lat, center.lng]} zoom={10} style={{ height: "100%", width: "100%" }} scrollWheelZoom>
        <TileLayer
          key={tileKey}
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          eventHandlers={{
            tileerror: handleTileError,
          }}
        />
        {collection.features.length ? (
          <GeoJSON
            key={colorMode + collection.features.length + (collection.features[0]?.properties?.ulpin || "")}
            data={collection}
            style={(feat) => ({
              color: featureColor(feat, colorMode),
              weight: 1.5,
              fillOpacity: 0.4,
              fillColor: featureColor(feat, colorMode),
            })}
            onEachFeature={(feat, layer) => {
              const p = feat.properties || {};
              layer.bindPopup(
                `<strong>${p.ulpin || "Parcel"}</strong><br/>${p.khasra_number || ""} · ${p.village || ""}<br/>${p.district_code || ""} ${p.state_code || ""}<br/>${p.area_ha != null ? p.area_ha + " ha" : ""} · ${p.acquisition_status || ""}<br/>Stage ${p.current_stage || "—"}<br/>Risk ${p.risk_score != null ? p.risk_score + "/100 " + (p.risk_level || "") : "unscored"}`,
              );
              if (onSelect) layer.on("click", () => onSelect(p));
            }}
          />
        ) : null}
        {bounds?.isValid() ? <Fit bounds={bounds} /> : null}
      </MapContainer>
    </div>
  );
}
