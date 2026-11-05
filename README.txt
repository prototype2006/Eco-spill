EcoSpill historical recommendation integration

Copy these files into your existing project:
- modules/incident_history.py
- modules/report_generator.py
- modules/incident_management.py (unchanged copy of your uploaded file)
- modules/recommendation_engine.py (new)

Ensure backend/oil_spill_case_library_15.csv exists. The engine expects the
CSV columns used by Blossom's code: case_id, incident_name, cause_category,
oil_type, spill_quantity, measures_taken, preventive_measures, source.

Recommendations are computed for display/PDF only and are not written to
Firebase. This is historical-case retrieval with text matching, not trained ML.
A sensor alert alone does not confirm an oil spill. Crew must verify suggestions.
