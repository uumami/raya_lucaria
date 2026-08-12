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
  const detail = document.querySelector("[data-raya-calendar-detail]");
  const detailTitle = document.querySelector("[data-raya-calendar-detail-title]");
  const detailEvents = document.querySelector("[data-raya-calendar-detail-events]");

  if (
    !root || !dataElement || !controls || !agenda || !grid
    || !detail || !detailTitle || !detailEvents
  ) return;

  const MAX_WIDE_DAY_EVENTS = 2;
  let calendarOpenerSequence = 0;

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

  function civilDateLabel(value) {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || ""));
    if (!match) return String(value || "");
    const year = Number(match[1]);
    const month = Number(match[2]);
    const day = Number(match[3]);
    const weekdays = [
      "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    ];
    const months = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December",
    ];
    return `${weekdays[mondayFirstWeekday(year, month, day)]}, `
      + `${months[month - 1]} ${day}, ${year}`;
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

  function calendarOpenerId(opener) {
    if (!opener.id) {
      calendarOpenerSequence += 1;
      opener.id = `raya-calendar-opener-${calendarOpenerSequence}`;
    }
    return opener.id;
  }

  function eventTimeText(event) {
    const start = typeof event.start_time === "string" ? event.start_time : "";
    const end = typeof event.end_time === "string" ? event.end_time : "";
    return start && end ? `${start}–${end}` : start || end;
  }

  function appendTextElement(parent, tagName, className, text) {
    if (!text) return null;
    const element = document.createElement(tagName);
    if (className) element.className = className;
    element.textContent = text;
    parent.appendChild(element);
    return element;
  }

  function appendDialogActions(article, event) {
    const pagePath = typeof event.page_output_path === "string"
      ? event.page_output_path
      : "";
    if (!pagePath) return;
    const actions = document.createElement("p");
    actions.className = "raya-calendar-actions";
    const pageLink = document.createElement("a");
    pageLink.className = "raya-calendar-open";
    const siteRoot = detail.getAttribute("data-raya-calendar-site-root") || "../../";
    const anchor = typeof event.anchor === "string" && event.anchor
      ? `#${encodeURIComponent(event.anchor)}`
      : "";
    pageLink.href = `${siteRoot}${pagePath}${anchor}`;
    pageLink.textContent = "Open page";
    actions.appendChild(pageLink);
    if (typeof event.page_id === "string" && event.page_id) {
      const graphLink = document.createElement("a");
      graphLink.className = "raya-calendar-graph";
      const graphHref = detail.getAttribute("data-raya-calendar-graph-href")
        || "../graph/index.html";
      graphLink.href = `${graphHref}?page=${encodeURIComponent(event.page_id)}`;
      graphLink.textContent = "View in graph";
      actions.appendChild(graphLink);
    }
    article.appendChild(actions);
  }

  function renderCalendarDialog(dialogEvents, opener) {
    detailEvents.replaceChildren();
    const date = dialogEvents.length > 0 ? String(dialogEvents[0].date || "") : "";
    detailTitle.textContent = date ? `Events for ${civilDateLabel(date)}` : "Calendar details";
    const selectedId = opener.getAttribute("data-raya-calendar-selected-id") || "";
    dialogEvents.forEach((event) => {
      const article = document.createElement("article");
      article.className = "raya-calendar-event raya-calendar-detail-event";
      article.setAttribute("data-raya-calendar-detail-event", String(event.id || ""));
      if (selectedId && event.id === selectedId) {
        article.setAttribute("data-raya-calendar-detail-selected", "true");
      }
      appendTextElement(
        article,
        "h3",
        "raya-calendar-detail-event-title",
        String(event.title || "Calendar event")
      );
      const kind = typeof event.kind === "string" ? calendarLabel(event.kind) : "Event";
      const type = typeof event.type === "string" ? calendarLabel(event.type) : "";
      const time = eventTimeText(event);
      appendTextElement(
        article,
        "p",
        "raya-calendar-detail-meta",
        [kind, type, time ? `Time: ${time}` : ""].filter(Boolean).join(" · ")
      );
      if (typeof event.summary === "string") {
        appendTextElement(
          article,
          "p",
          "raya-calendar-event-summary",
          event.summary
        );
      }
      if (Array.isArray(event.tags) && event.tags.length > 0) {
        const tags = document.createElement("ul");
        tags.className = "raya-calendar-tags";
        tags.setAttribute("aria-label", "Tags");
        event.tags.forEach((tag) => appendTextElement(tags, "li", "", String(tag)));
        article.appendChild(tags);
      }
      appendDialogActions(article, event);
      detailEvents.appendChild(article);
    });
  }

  function calendarLabel(value) {
    return String(value || "")
      .replaceAll("-", " ")
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function openCalendarDetail(date, opener, selectedId) {
    const dialogEvents = visibleEvents().filter((event) => event.date === date);
    opener.setAttribute("data-raya-calendar-selected-id", selectedId || "");
    renderCalendarDialog(dialogEvents, opener);
    detail.dataset.rayaCalendarOpener = calendarOpenerId(opener);
    if (!detail.open) detail.showModal();
  }

  function appendGridEvent(cell, event, date) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "raya-calendar-grid-event";
    button.setAttribute("data-raya-calendar-event-open", String(event.id || ""));
    calendarOpenerId(button);
    const title = String(event.title || "Calendar event");
    const kind = typeof event.kind === "string" ? calendarLabel(event.kind) : "Event";
    const time = eventTimeText(event);
    button.setAttribute(
      "aria-label",
      `Open ${title}, ${kind}${time ? `, ${time}` : ""} on ${civilDateLabel(date)}`
    );
    appendTextElement(button, "span", "raya-calendar-grid-event-kind", kind);
    appendTextElement(button, "span", "raya-calendar-grid-event-title", title);
    button.addEventListener("click", () => openCalendarDetail(date, button, event.id));
    cell.appendChild(button);
  }

  function appendCalendarOverflow(cell, date, hiddenCount) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "raya-calendar-overflow";
    button.setAttribute("data-raya-calendar-overflow", "");
    calendarOpenerId(button);
    button.textContent = `+${hiddenCount} more`;
    button.setAttribute(
      "aria-label",
      `Show ${hiddenCount} more events for ${civilDateLabel(date)}`
    );
    button.addEventListener("click", () => openCalendarDetail(date, button, ""));
    cell.appendChild(button);
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
          const dayEvents = byDate.get(date) || [];
          dayEvents
            .slice(0, MAX_WIDE_DAY_EVENTS)
            .forEach((event) => appendGridEvent(cell, event, date));
          if (dayEvents.length > MAX_WIDE_DAY_EVENTS) {
            appendCalendarOverflow(
              cell,
              date,
              dayEvents.length - MAX_WIDE_DAY_EVENTS
            );
          }
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
