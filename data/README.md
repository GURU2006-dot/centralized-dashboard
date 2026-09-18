# Prototype data — SYNTHETIC ONLY

Every CSV, GeoJSON feature, owner name, ULPIN, khasra, coordinate, rupee figure, and ML score in this directory and in the seeded database is **synthetic demonstration data**.

- ULPINs are prefixed `SYN` and are **not** Unique Land Parcel Identification Numbers issued by DoLR.
- Geometries are generated rectangles around public city centroids. They are **not** cadastral maps.
- Owner ID numbers, phones, and addresses are fake and must not be shown in general parcel APIs (Phase 2+).
- `data_source` on operational rows is `SYNTHETIC`.

Do not present this dataset as live government land records.
