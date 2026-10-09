"""Pandas stand-in for the Cypher calls, so parsing/routing logic can be tested
without a Neo4j server. It mirrors the semantics of the real Cypher queries
(same ordering, same amount>0 filter, same per-nutrient top-N)."""
import re

from graph import schema
from graph.category_resolver import resolve_categories
from graph.graph_retriever import GraphRetriever, food_patterns
from graph.seed_knowledge import GOAL_BY_KEY, SUPPORTS

DT_RANK = {"foundation_food": 0, "sr_legacy_food": 1}


class FakeRetriever(GraphRetriever):
    def __init__(self, df, tmp_raw):
        self.df = df
        self.cats = resolve_categories(df, tmp_raw, "name-prefix")
        self._category_cache = None

    def category_names(self):
        return sorted({c for c, _ in self.cats.values()})

    def _amount_rows(self, sub, keys, include_zero):
        rows = []
        for r in sub.itertuples(index=False):
            for nd in schema.NUTRIENTS:
                v = getattr(r, nd.column)
                if v != v or (keys is not None and nd.key not in keys) or (not include_zero and not v > 0):
                    continue
                rows.append(dict(fdc_id=r.fdc_id, food=r.food_name, data_type=r.data_type, nutrient=nd.name,
                                 nutrient_key=nd.key, amount=float(v), unit=nd.unit,
                                 basis=schema.AMOUNT_BASIS, source=schema.USDA_SOURCE))
        return rows

    def find_foods(self, tokens, limit):
        pats = [re.compile(p[2:-2] if False else p) for p in food_patterns(tokens)]
        m = self.df[self.df.food_name.str.lower().map(lambda s: all(p.fullmatch(s) for p in pats))]
        m = m.assign(_r=m.data_type.map(lambda d: DT_RANK.get(d, 2)), _l=m.food_name.str.len())
        m = m.sort_values(["_r", "_l", "food_name"])
        foods = [dict(fdc_id=int(r.fdc_id), name=r.food_name, data_type=r.data_type) for r in m.head(limit).itertuples()]
        return len(m), foods

    def food_nutrients(self, fdc_ids, nutrient_keys=None, include_zero=False):
        return self._amount_rows(self.df[self.df.fdc_id.isin(fdc_ids)], nutrient_keys, include_zero)

    def nutrient_foods(self, key, limit, ascending=False):
        rows = self._amount_rows(self.df, [key], True)
        rows.sort(key=lambda r: ((r["amount"] if ascending else -r["amount"]), r["food"]))
        return rows[:limit]

    def food_categories(self, fdc_ids):
        names = dict(zip(self.df.fdc_id, self.df.food_name))
        return [dict(fdc_id=i, food=names[i], category=self.cats[i][0], category_source=self.cats[i][1]) for i in fdc_ids]

    def category_foods(self, category, limit):
        names = dict(zip(self.df.fdc_id, self.df.food_name))
        ids = sorted((i for i, (c, _) in self.cats.items() if c == category), key=lambda i: names[i])
        return len(ids), [dict(fdc_id=i, food=names[i], category_source=self.cats[i][1]) for i in ids[:limit]]

    def goal_nutrients(self, goal_keys):
        out = []
        for nk, gk, basis in SUPPORTS:
            if gk in goal_keys:
                out.append(dict(goal=GOAL_BY_KEY[gk][1], goal_key=gk, nutrient=schema.NUTRIENT_BY_KEY[nk].name,
                                nutrient_key=nk, basis=basis, curated=True, curation_source="manual_curation"))
        return out

    def goal_foods(self, goal_keys, per_nutrient_limit):
        out = []
        for nk, gk, basis in SUPPORTS:
            if gk not in goal_keys:
                continue
            for r in self.nutrient_foods(nk, per_nutrient_limit):
                out.append(dict(goal=GOAL_BY_KEY[gk][1], goal_key=gk, nutrient=r["nutrient"], nutrient_key=nk,
                                food=r["food"], fdc_id=r["fdc_id"], amount=r["amount"], unit=r["unit"],
                                basis=basis, curation_source="manual_curation"))
        return out
