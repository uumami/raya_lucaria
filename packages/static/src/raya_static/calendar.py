from __future__ import annotations

from dataclasses import dataclass


CALENDAR_SCRIPT_NAME = "calendar.js"
CALENDAR_RESOURCE_PATH = "_raya/render"


@dataclass(frozen=True)
class CalendarResources:
    javascript: str


def calendar_resources() -> CalendarResources:
    return CalendarResources(javascript=_CALENDAR_JAVASCRIPT)


_CALENDAR_JAVASCRIPT = r"""
(() => {
  const root = document.querySelector("[data-raya-calendar-page]");
  const dataElement = document.getElementById("raya-calendar-data");
  const controls = document.querySelector("[data-raya-calendar-controls]");
  const agenda = document.querySelector("[data-raya-calendar-agenda]");
  const grid = document.querySelector("[data-raya-calendar-grid]");
  const status = document.querySelector("[data-raya-calendar-status]");
  const summary = document.querySelector("[data-raya-calendar-summary-count]");
  const pageFocus = document.querySelector("[data-raya-calendar-page-focus]");
  const clear = document.querySelector("[data-raya-calendar-clear]");
  const viewButtons = Array.from(
    document.querySelectorAll("[data-raya-calendar-view]")
  );
  const kindButtons = Array.from(
    document.querySelectorAll("[data-raya-calendar-kind-filter]")
  );
  const typeButtons = Array.from(
    document.querySelectorAll("[data-raya-calendar-type-filter]")
  );
  const previous = document.querySelector("[data-raya-calendar-prev]");
  const next = document.querySelector("[data-raya-calendar-next]");
  const todayButton = document.querySelector("[data-raya-calendar-today]");

  if (!root || !dataElement || !controls || !agenda || !grid) return;

  let payload;
  try {
    payload = JSON.parse(dataElement.textContent || "{}");
  } catch {
    if (status) status.textContent = "Calendar data could not be read.";
    return;
  }

  const events = Array.isArray(payload.events)
    ? payload.events.filter((event) => event && typeof event === "object")
    : [];
  const timeZone = typeof payload.timezone === "string" ? payload.timezone : "UTC";
  const agendaItems = new Map();
  document.querySelectorAll("[data-raya-calendar-event]").forEach((eventElement) => {
    const id = eventElement.getAttribute("data-raya-calendar-event") || "";
    const item = eventElement.closest(".raya-calendar-event-item") || eventElement;
    if (id && !agendaItems.has(id)) agendaItems.set(id, { eventElement, item });
  });

  function civilToday(zone, now = new Date()) {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: zone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).formatToParts(now);
    const values = Object.fromEntries(
      parts
        .filter(({ type }) => type !== "literal")
        .map(({ type, value }) => [type, value])
    );
    return `${values.year}-${values.month}-${values.day}`;
  }

  function validCivilDate(value) {
    return /^\d{4}-\d{2}-\d{2}$/.test(String(value || ""));
  }

  function civilMonth(value) {
    return validCivilDate(value) ? String(value).slice(0, 7) : "";
  }

  function parseMonth(value) {
    const match = /^(\d{4})-(\d{2})$/.exec(value);
    return match ? { year: Number(match[1]), month: Number(match[2]) } : null;
  }

  function monthValue(year, month) {
    return `${String(year).padStart(4, "0")}-${String(month).padStart(2, "0")}`;
  }

  function shiftMonth(value, amount) {
    const parsed = parseMonth(value);
    if (!parsed) return value;
    let year = parsed.year;
    let month = parsed.month + amount;
    while (month < 1) {
      year -= 1;
      month += 12;
    }
    while (month > 12) {
      year += 1;
      month -= 12;
    }
    return monthValue(year, month);
  }

  function isLeapYear(year) {
    return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  }

  function daysInMonth(year, month) {
    if (month === 2) return isLeapYear(year) ? 29 : 28;
    return [4, 6, 9, 11].includes(month) ? 30 : 31;
  }

  function mondayFirstWeekday(year, month, day) {
    const offsets = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4];
    const adjustedYear = month < 3 ? year - 1 : year;
    const sundayFirst = (
      adjustedYear
      + Math.floor(adjustedYear / 4)
      - Math.floor(adjustedYear / 100)
      + Math.floor(adjustedYear / 400)
      + offsets[month - 1]
      + day
    ) % 7;
    return (sundayFirst + 6) % 7;
  }

  const today = civilToday(timeZone);
  const todayMonth = civilMonth(today);
  const eventMonths = Array.from(
    new Set(events.map((event) => civilMonth(event.date)).filter(Boolean))
  ).sort();
  let displayedMonth = eventMonths.includes(todayMonth)
    ? todayMonth
    : eventMonths.find((month) => month > todayMonth)
      || eventMonths[eventMonths.length - 1]
      || todayMonth;
  let activeView = "agenda";
  let activeKind = "all";
  let activeType = "all";
  let activePage = "";
  try {
    const requestedPage = new URLSearchParams(window.location.search || "").get("page") || "";
    if (requestedPage && events.some((event) => event.page_id === requestedPage)) {
      activePage = requestedPage;
    }
  } catch {
    activePage = "";
  }

  function eventMatchesPage(event) {
    return !activePage
      || event.page_id === activePage
      || (!event.page_id && ["holiday", "milestone"].includes(event.kind));
  }

  function eventIsVisible(event) {
    return eventMatchesPage(event)
      && (activeKind === "all" || event.kind === activeKind)
      && (activeType === "all" || event.type === activeType);
  }

  function visibleEvents() {
    return events.filter(eventIsVisible);
  }

  function monthLabel(value) {
    const parsed = parseMonth(value);
    if (!parsed) return value;
    const names = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December",
    ];
    return `${names[parsed.month - 1]} ${parsed.year}`;
  }

  function countText(count) {
    return `${count} visible calendar ${count === 1 ? "event" : "events"}.`;
  }

  function matchingCountText(count) {
    return `${count} matching ${count === 1 ? "event" : "events"} across the calendar.`;
  }

  function monthStatusText(shownCount, matchingCount) {
    return `${shownCount} ${shownCount === 1 ? "event" : "events"} shown in `
      + `${monthLabel(displayedMonth)}. ${matchingCountText(matchingCount)}`;
  }

  function updatePressedState() {
    viewButtons.forEach((button) => {
      button.setAttribute(
        "aria-pressed",
        button.getAttribute("data-raya-calendar-view") === activeView ? "true" : "false"
      );
    });
    kindButtons.forEach((button) => {
      button.setAttribute(
        "aria-pressed",
        button.getAttribute("data-raya-calendar-kind-filter") === activeKind
          ? "true"
          : "false"
      );
    });
    typeButtons.forEach((button) => {
      button.setAttribute(
        "aria-pressed",
        button.getAttribute("data-raya-calendar-type-filter") === activeType
          ? "true"
          : "false"
      );
    });
  }

  function updateAgenda(visible) {
    const visibleIds = new Set(visible.map((event) => event.id));
    agendaItems.forEach(({ item }, id) => {
      item.hidden = !visibleIds.has(id);
    });
    agenda.querySelectorAll(".raya-calendar-month").forEach((month) => {
      month.hidden = !Array.from(
        month.querySelectorAll(".raya-calendar-event-item")
      ).some((item) => !item.hidden);
    });
  }

  function appendGridEvent(cell, event) {
    const agendaItem = agendaItems.get(event.id);
    if (!agendaItem) return;
    const clone = agendaItem.eventElement.cloneNode(true);
    clone.classList.add("raya-calendar-grid-event");
    clone.querySelector(".raya-calendar-date")?.remove();
    cell.appendChild(clone);
  }

  function renderMonth(visible) {
    grid.replaceChildren();
    const parsed = parseMonth(displayedMonth);
    if (!parsed) return;

    const table = document.createElement("table");
    const caption = document.createElement("caption");
    caption.setAttribute("data-raya-calendar-month-caption", "");
    caption.textContent = monthLabel(displayedMonth);
    table.appendChild(caption);

    const head = document.createElement("thead");
    const headRow = document.createElement("tr");
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
      .forEach((label) => {
        const header = document.createElement("th");
        header.scope = "col";
        header.textContent = label;
        headRow.appendChild(header);
      });
    head.appendChild(headRow);
    table.appendChild(head);

    const body = document.createElement("tbody");
    const leading = mondayFirstWeekday(parsed.year, parsed.month, 1);
    const dayCount = daysInMonth(parsed.year, parsed.month);
    const cellCount = Math.ceil((leading + dayCount) / 7) * 7;
    const byDate = new Map();
    visible.forEach((event) => {
      if (civilMonth(event.date) !== displayedMonth) return;
      if (!byDate.has(event.date)) byDate.set(event.date, []);
      byDate.get(event.date).push(event);
    });

    for (let offset = 0; offset < cellCount; offset += 7) {
      const row = document.createElement("tr");
      for (let column = 0; column < 7; column += 1) {
        const cell = document.createElement("td");
        const day = offset + column - leading + 1;
        if (day >= 1 && day <= dayCount) {
          const date = `${displayedMonth}-${String(day).padStart(2, "0")}`;
          cell.setAttribute("data-raya-calendar-date", date);
          const dayNumber = document.createElement("span");
          dayNumber.className = "raya-calendar-day-number";
          dayNumber.textContent = String(day);
          cell.appendChild(dayNumber);
          if (date === today) {
            cell.setAttribute("aria-current", "date");
            const todayLabel = document.createElement("span");
            todayLabel.className = "raya-calendar-today-label";
            todayLabel.textContent = "Today";
            cell.appendChild(todayLabel);
          }
          (byDate.get(date) || []).forEach((event) => appendGridEvent(cell, event));
        } else {
          cell.className = "raya-calendar-outside-month";
          cell.setAttribute("aria-hidden", "true");
        }
        row.appendChild(cell);
      }
      body.appendChild(row);
    }
    table.appendChild(body);
    grid.appendChild(table);
  }

  function updatePageFocus(visibleCount) {
    if (!pageFocus) return;
    pageFocus.hidden = !activePage;
    pageFocus.textContent = activePage
      ? `Focused on page ${activePage}. ${matchingCountText(visibleCount)} Use Clear to show all.`
      : "";
  }

  function render() {
    const visible = visibleEvents();
    const shownInMonth = visible.filter(
      (event) => civilMonth(event.date) === displayedMonth
    ).length;
    updatePressedState();
    updateAgenda(visible);
    renderMonth(visible);
    agenda.hidden = activeView !== "agenda";
    grid.hidden = activeView !== "month";
    const viewStatus = activeView === "month"
      ? monthStatusText(shownInMonth, visible.length)
      : countText(visible.length);
    if (summary) summary.textContent = viewStatus;
    if (status) status.textContent = viewStatus;
    updatePageFocus(visible.length);
  }

  function removePageQuery() {
    try {
      const url = new URL(window.location.href);
      url.searchParams.delete("page");
      window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
      if (typeof window.rayaSyncCourseMapPageFocus === "function") {
        window.rayaSyncCourseMapPageFocus();
      }
    } catch {
      // The Calendar remains useful even when URL mutation is unavailable.
    }
  }

  function clearCalendar({ focus = false } = {}) {
    activeKind = "all";
    activeType = "all";
    activePage = "";
    removePageQuery();
    render();
    if (focus && clear) clear.focus();
  }

  viewButtons.forEach((button) => {
    button.addEventListener("click", () => {
      activeView = button.getAttribute("data-raya-calendar-view") || "agenda";
      render();
    });
  });
  kindButtons.forEach((button) => {
    button.addEventListener("click", () => {
      activeKind = button.getAttribute("data-raya-calendar-kind-filter") || "all";
      render();
    });
  });
  typeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      activeType = button.getAttribute("data-raya-calendar-type-filter") || "all";
      render();
    });
  });
  previous?.addEventListener("click", () => {
    displayedMonth = shiftMonth(displayedMonth, -1);
    render();
  });
  next?.addEventListener("click", () => {
    displayedMonth = shiftMonth(displayedMonth, 1);
    render();
  });
  todayButton?.addEventListener("click", () => {
    displayedMonth = todayMonth;
    render();
  });
  clear?.addEventListener("click", () => clearCalendar());
  root.addEventListener("keydown", (event) => {
    const hasCalendarConstraint = activeKind !== "all"
      || activeType !== "all"
      || Boolean(activePage);
    if (event.key !== "Escape" || event.defaultPrevented || !hasCalendarConstraint) {
      return;
    }
    event.preventDefault();
    clearCalendar({ focus: true });
  });

  controls.hidden = false;
  root.setAttribute("data-raya-calendar-enhanced", "true");
  render();
})();
"""
