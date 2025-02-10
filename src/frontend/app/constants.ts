export const CHART_RANGES = {
  hour: {
    tickformat: "%H:%M",
    momentFormat: "HH:mm",
    momentValue: "minute",
    hoverRange:
      "%{customdata.start|%Y/%m/%d %H:%M:00} - %{customdata.end|%Y/%m/%d %H:%M:59}",
    groupFormat: "YYYY-MM-DD HH:mm",
  },
  day: {
    tickformat: "%H",
    momentFormat: "HH:mm",
    momentValue: "day",
    hoverRange:
      "%{customdata.start|%Y/%m/%d %H:00:00} - %{customdata.end|%Y/%m/%d %H:59:59}",
    groupFormat: "YYYY-MM-DD",
  },
  month: {
    tickformat: "%d",
    momentFormat: "DD",
    momentValue: "day",
    hoverRange:
      "%{customdata.start|%Y/%m/%d 00:00:00} - %{customdata.end|%Y/%m/%d 23:59:59}",
    groupFormat: "YYYY-MM-DD",
  },
  year: {
    tickformat: "%B",
    momentFormat: "MMMM",
    momentValue: "year",
    hoverRange:
      "%{customdata.start|%Y/%m/%d 00:00:00} - %{customdata.end|%Y/%m/%d 23:59:59}",
    groupFormat: "YYYY-MM",
  },
};