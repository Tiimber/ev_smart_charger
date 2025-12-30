# Dashboard cards

## Sample card with typical information

A graph showing planned charging time, followed by a summary of it in text. Then follows some standard settings as well as "one-time" overrides.

[![Sample Dashboard Card](./dashboard_card_typical_small.png)](./dashboard_card_typical_full.png)

[YAML code](./lovelace_example.yaml)

## Interactive charging graph

Only the graph, showing the planned charging time. Interactive version that allows showing a bit more info on hovering.

[![Charging graph](./dashboard_charging_graph_small.png)](./dashboard_charging_graph_full.png)

[YAML code](./lovelace_example_graph.yaml)

## Summary of planned charging (text)

Only the summary text of the planned charging.

[![Summary text](./dashboard_summary_section_small.png)](./dashboard_summary_section_full.png)

[YAML code](./lovelace_example_summary.yaml)

## Settings

The settings, default and overrides.

[![Settings and overrides](./dashboard_settings_and_overrides_small.png)](./dashboard_settings_and_overrides_full.png)

[YAML code](./lovelace_example_settings_and_overrides.yaml)

## Action Log

The log of what actions was taken. This shows an extensive log including timestamps of when charging started/stopped, what amps were set for the charger, car being plugged in or unplugged, and more.

[![Action Log](./dashboard_action_log_small.png)](./dashboard_action_log_full.png)

[YAML code](./lovelace_example_action_log.yaml)

## Charging Plan

An image showing the current charging plan for the entire window it knows the electricity price, with a button to re-generate it. Shows a line for expected car charge level at each time, the price bars for each time interval and black bars for when the charger will be on (charging and maintenance mode). Image can be downloaded to eg. be printed on a thermal printer. (Can be used as a more lightweight graph than the ApexChart version above)

[![Charging Plan](./dashboard_charging_plan_small.png)](./dashboard_charging_plan_full.png)

[YAML code](./lovelace_example_charging_plan.yaml)

## Charging Report

An image showing the last carried out charging session, with a button to generate it instantly, instead of when car is unplugged. Shows a line for the cars charge level (estimated and/or real value), price bars for the electricity price and black bars for when the charger was actively charging. Image can be downloaded to eg. be printed on a thermal printer.

(Sorry, but sample image only shows a short snapshot without any recorded charging data, but also shows that it handles when no charging was carried out.)

[![Charging Report](./dashboard_charging_report_small.png)](./dashboard_charging_report_full.png)

[YAML code](./lovelace_example_charging_report.yaml)
