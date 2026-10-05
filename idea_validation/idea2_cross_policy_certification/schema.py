FIELDS={"era_id","state","action","outcome"}
def validate(rows):
 for r in rows:
  if set(r)!=FIELDS:raise ValueError("oracle or missing field")
