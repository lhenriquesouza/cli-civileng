"""Extract structured project data from ArchiCAD SAF XLSX exports."""
import openpyxl


def _polygon_area(coords: list[tuple[float, float, float]]) -> float:
    """Calculate 2D polygon area using shoelace formula (XY plane)."""
    if len(coords) < 3:
        return 0.0
    area = 0.0
    for i in range(len(coords)):
        x1, y1, _ = coords[i]
        x2, y2, _ = coords[(i + 1) % len(coords)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2


def extract_project_data(xlsx_path: str) -> dict:
    """Extract compliance-relevant data from ArchiCAD SAF XLSX.

    Returns dict with:
      - max_height: max Z coordinate from structural nodes
      - building_footprint_area: projection area from ground-floor surfaces
      - floor_areas_total: summed area of all floor/slab surfaces
      - layers: list of layer names found
      - structural_elements: counts of beams, columns, slabs
    """
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)

    result = {
        "building_footprint_area": 0.0,
        "floor_areas_total": 0.0,
        "max_height": 0.0,
        "layers": set(),
        "structural_elements": {"beams": 0, "columns": 0, "slabs": 0},
    }

    # Build node map — col 0=Name, 1=X, 2=Y, 3=Z
    nodes = {}
    if "StructuralPointConnection" in wb.sheetnames:
        ws = wb["StructuralPointConnection"]
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[0] and row[1] is not None:
                nodes[row[0]] = (
                    float(row[1]),
                    float(row[2]),
                    float(row[3]) if row[3] else 0,
                )
        if nodes:
            result["max_height"] = max(n[2] for n in nodes.values())

    # Surface members — col 0=Name, 6=Nodes, 10=Layer, 4=Thickness
    if "StructuralSurfaceMember" in wb.sheetnames:
        ws = wb["StructuralSurfaceMember"]
        footprint_areas = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            name = row[0]
            node_str = row[6] or ""
            layer = str(row[10]).strip() if row[10] else ""
            thickness = float(row[4]) if row[4] else 0

            result["layers"].add(layer)

            node_names = [n.strip() for n in str(node_str).split(";") if n.strip()]
            coords = [nodes[n] for n in node_names if n in nodes]

            if coords and len(coords) >= 3:
                area = _polygon_area(coords)

                # Classify: floors/slabs vs other
                if "Piso" in layer or "Laje" in layer:
                    result["structural_elements"]["slabs"] += 1
                    result["floor_areas_total"] += area

                    # Ground floor approximation: lowest Z surfaces
                    z_avg = sum(c[2] for c in coords) / len(coords)
                    if z_avg < 1.5:  # ground level
                        footprint_areas.append(area)

        # Building footprint: sum of ground-level floors
        if footprint_areas:
            result["building_footprint_area"] = round(sum(footprint_areas), 1)

    # Curve members — col 1=Type, 10=Layer
    if "StructuralCurveMember" in wb.sheetnames:
        ws = wb["StructuralCurveMember"]
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[1] and row[10]:
                element_type = str(row[1])
                result["layers"].add(str(row[10]))
                if element_type == "Beam":
                    result["structural_elements"]["beams"] += 1
                elif element_type == "Column":
                    result["structural_elements"]["columns"] += 1

    result["layers"] = sorted(result["layers"])
    result["building_footprint_area"] = round(result["building_footprint_area"], 1)
    result["floor_areas_total"] = round(result["floor_areas_total"], 1)
    result["max_height"] = round(result["max_height"], 2)

    return result
