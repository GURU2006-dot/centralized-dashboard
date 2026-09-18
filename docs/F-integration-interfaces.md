# F. Integration interfaces

Requirement 11 asks for **API-based integration architecture**, not live government connectivity.

**No government API URLs, keys, or schemas are invented as if they were real.**  
Adapters speak a **stable internal contract**. Implementations are mock for the prototype.

---

## 1. Pipeline

```
External Government System     (not available in SIH lab)
        ↓
Integration Adapter            (Protocol in app/integrations/base.py)
        ↓
Data Validation                (Pydantic / adapter-level)
        ↓
Data Normalization             (Internal DTOs)
        ↓
Internal Service               (parcel_service, gis_service, …)
        ↓
PostgreSQL                     (data_source = MOCK_ADAPTER | SYNTHETIC)
        ↓
FastAPI
        ↓
Frontend                       (Badge: MOCK / SYNTHETIC — never “Live DoLR”)
```

`INTEGRATION_MODE=mock` (default) | `external` (always fails closed with 503 unless a real adapter is later implemented).

---

## 2. Availability register (honest)

| Adapter | Real-world system (name only) | Public SIH access | Classification | Prototype implementation |
|---|---|---|---|---|
| Land records | DILRMP / state land records / ULPIN | Not publicly consumable | **UNAVAILABLE_PUBLIC** + **REQUIRES_AUTHORIZATION** | `MockLandRecordsAdapter` |
| Cadastral maps | BhuNaksha / state GIS WMS/WFS | Not publicly consumable | **UNAVAILABLE_PUBLIC** + **REQUIRES_AUTHORIZATION** | `MockCadastralAdapter` |
| Registration | NGDRS / SRO | Not publicly consumable | **UNAVAILABLE_PUBLIC** + **REQUIRES_AUTHORIZATION** | `MockRegistrationAdapter` |
| Acquisition MIS | State/central acquisition portals | Not publicly consumable | **UNAVAILABLE_PUBLIC** + **REQUIRES_AUTHORIZATION** | `MockAcquisitionDataAdapter` |
| OSM tiles | OpenStreetMap | **AVAILABLE_VERIFIED** (public tiles) | Basemap only — **not** an adapter for cadastral truth | Leaflet tile URL |

`AVAILABLE_VERIFIED` is used **only** for OSM basemap in the frontend config, not for parcel geometry.

---

## 3. Internal DTOs (`app/integrations/base.py`)

These are the **only** shapes services depend on.

```text
NormalizedParcel
  ulpin: str
  khasra_number: str
  village: str
  tehsil: str
  state_code: str
  district_code: str
  area_ha: float
  owners: list[NormalizedOwner]
  data_source: Literal["MOCK_ADAPTER","EXTERNAL"]
  fetched_at: datetime
  raw_reference: str          # mock id or future external request id — not a fake gov URL

NormalizedOwner
  name: str
  share_pct: float | None
  ownership_type: str | None

NormalizedCadastralFeature
  ulpin: str
  geometry_geojson: dict      # RFC 7946
  srid: int                   # 4326
  data_source: Literal["MOCK_ADAPTER","EXTERNAL"]
  disclaimer: str

NormalizedRegistration
  ulpin: str
  last_deed_date: date | None
  last_deed_type: str | None
  data_source: Literal["MOCK_ADAPTER","EXTERNAL"]

NormalizedAcquisitionSnapshot
  project_code: str
  notified_area_ha: float | None
  acquired_area_ha: float | None
  data_source: Literal["MOCK_ADAPTER","EXTERNAL"]

AdapterHealth
  name: str
  implementation: Literal["MOCK","EXTERNAL"]
  availability: Literal["AVAILABLE_VERIFIED","REQUIRES_AUTHORIZATION","UNAVAILABLE_PUBLIC","MOCK_ONLY"]
  requires_authorization: bool
  healthy: bool
  message: str
```

Validation: ulpin length 1–14, area_ha > 0, GeoJSON type Polygon/MultiPolygon, state_code in `states` table. Failures raise `AdapterValidationError` → HTTP 400.

---

## 4. Protocol (standardized internal interface)

Every adapter implements:

```text
class LandRecordsPort:
    name = "land_records"
    def health() -> AdapterHealth
    def lookup(*, ulpin: str | None, state_code: str | None,
               district_code: str | None, khasra_number: str | None) -> NormalizedParcel

class CadastralMapPort:
    name = "cadastral_maps"
    def health() -> AdapterHealth
    def get_parcel_geometry(ulpin: str) -> NormalizedCadastralFeature

class RegistrationPort:
    name = "registration"
    def health() -> AdapterHealth
    def lookup_by_ulpin(ulpin: str) -> NormalizedRegistration

class AcquisitionDataPort:
    name = "acquisition_data"
    def health() -> AdapterHealth
    def snapshot(project_code: str) -> NormalizedAcquisitionSnapshot
```

`factory.py`:

```text
if settings.INTEGRATION_MODE == "mock":
    return MockLandRecordsAdapter(...)
else:
    return ExternalLandRecordsAdapter(...)  # not implemented → NotImplementedAdapter (503)
```

---

## 5. Mock adapters

**Data:** read from `data/seed/*.csv` and `data/geo/parcels.geojson` already in the database **or** a small in-memory map loaded at startup from the same CSVs. Prefer DB so mock lookup of a seeded ULPIN returns that parcel and stamps `data_source=MOCK_ADAPTER` on the **response** (does not silently reclassify stored `SYNTHETIC` rows unless the service explicitly imports).

**Behaviour:**

- Known ULPIN → 200 normalized DTO, `data_source=MOCK_ADAPTER`.
- Unknown → adapter-level not found → HTTP 404.
- 150–300 ms `asyncio.sleep` optional to simulate latency (keep **off** by default so demos are snappy; enable via `MOCK_ADAPTER_LATENCY_MS`).
- `health().availability = UNAVAILABLE_PUBLIC`, `implementation = MOCK`, `healthy = true`, message: *“No public API. Mock adapter serving synthetic records.”*

**External*Adapter (stubs):** `health().healthy = false`, `requires_authorization = true`, lookup raises `IntegrationUnavailable`. **No fabricated base URLs.**

---

## 6. HTTP surface (prototype)

See API contracts §17:

- `GET /api/integrations/status` — honest register for judges.
- `POST /api/integrations/land-records/lookup`
- `POST /api/integrations/cadastral/parcel`
- `GET /api/integrations/health`

Admin UI shows four cards with **MOCK** badges. Copy on the page:

> Government land-record, cadastral, registration, and acquisition-MIS APIs require departmental authorization and are not connected. The adapters below use the same internal interfaces a future authorized connection would use.

---

## 7. Swap path (after SIH)

1. Implement `ExternalLandRecordsAdapter` against a **real, documented, authorized** spec.
2. Keep `LandRecordsPort` unchanged.
3. Set credentials in env; `INTEGRATION_MODE=external`.
4. Persist imports with `data_source=EXTERNAL`.
5. Frontend Badge already branches on `data_source`.

No router or React page change required beyond the status payload becoming `AVAILABLE_VERIFIED` when that is actually true.
