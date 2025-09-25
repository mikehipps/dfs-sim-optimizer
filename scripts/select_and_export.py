import pandas as pd

from optimizer.selector import (
    SelectorConfig, load_players_csv, load_candidates_csv,
    select_portfolio, export_selected, exposures_report
)

METRICS_CSV    = "lineup_metrics.csv"
CANDIDATES_CSV = "candidates.csv"
PLAYERS_CSV    = "players.csv"

metrics      = pd.read_csv(METRICS_CSV)
lineups_pid  = load_candidates_csv(CANDIDATES_CSV)
players_by_id= load_players_csv(PLAYERS_CSV)

cfg = SelectorConfig(
    portfolio_size=150,
    global_exposure_cap=0.35,
    per_player_caps=None,
    uniqueness_k=2,
    objective="p99",
    secondary_objective="top_1pct_rate",
    secondary_weight=0.2,
    by="player_id"
)

selected = select_portfolio(metrics, lineups_pid, players_by_id, cfg)
print(f"Selected {len(selected)} lineups.")

export_selected(selected, lineups_pid, players_by_id, "fd_upload.csv", by=cfg.by)

exp_df = exposures_report(selected, lineups_pid, players_by_id)
exp_df.to_csv("portfolio_exposures.csv", index=False)
metrics.iloc[selected].assign(selected_rank=range(1, len(selected)+1)) \
       .to_csv("portfolio_metrics.csv", index=False)

print("Wrote fd_upload.csv, portfolio_exposures.csv, portfolio_metrics.csv")
