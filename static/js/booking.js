/**
 * CutZone booking page script.
 *
 * Handles the guided flow: choose service → choose barber → choose date
 * → load available times via AJAX → confirm.
 *
 * NOTE: this is convenience only. All rules are re-validated on the
 * backend (bookings/availability.py) when the form is submitted.
 */

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("booking-form");
  if (!form) return;

  const serviceInput = document.getElementById("id_service");
  const barberInput = document.getElementById("id_barber");
  const dateInput = document.getElementById("id_date");
  const timeInput = document.getElementById("id_start_time");
  const slotsBox = document.getElementById("slots-box");
  const slotsHint = document.getElementById("slots-hint");
  const submitBtn = document.getElementById("submit-btn");
  const summaryBox = document.getElementById("summary-box");
  const slotsUrl = form.dataset.slotsUrl;
  const excludeId = form.dataset.exclude || "";

  // ---- card selection (service & barber) --------------------------------
  document.querySelectorAll(".choice-card[data-target]").forEach(function (card) {
    card.addEventListener("click", function () {
      const targetId = card.dataset.target;
      const input = document.getElementById(targetId);
      input.value = card.dataset.value;
      // Highlight only the clicked card within its group.
      document
        .querySelectorAll('.choice-card[data-target="' + targetId + '"]')
        .forEach(function (c) { c.classList.remove("selected"); });
      card.classList.add("selected");
      refreshSlots();
      updateSummary();
    });
  });

  if (dateInput) {
    dateInput.addEventListener("change", function () {
      refreshSlots();
      updateSummary();
    });
  }

  // ---- fetch available slots from the backend ---------------------------
  function refreshSlots() {
    timeInput.value = "";
    submitBtn.disabled = true;
    slotsBox.innerHTML = "";

    const service = serviceInput.value;
    const barber = barberInput.value;
    const date = dateInput.value;

    if (!service || !barber || !date) {
      slotsHint.textContent = "Select a service, barber and date to see available times.";
      return;
    }

    slotsHint.textContent = "Loading available times…";
    const params = new URLSearchParams({ service: service, barber: barber, date: date });
    if (excludeId) params.append("exclude", excludeId);

    fetch(slotsUrl + "?" + params.toString(), {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        slotsBox.innerHTML = "";
        if (!data.slots || data.slots.length === 0) {
          slotsHint.textContent =
            "No available times on this date. Please try another day.";
          return;
        }
        slotsHint.textContent = "Choose a time:";
        data.slots.forEach(function (slot) {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "slot-btn";
          btn.textContent = slot.label;
          btn.dataset.value = slot.value;
          btn.addEventListener("click", function () {
            slotsBox.querySelectorAll(".slot-btn").forEach(function (b) {
              b.classList.remove("selected");
            });
            btn.classList.add("selected");
            timeInput.value = slot.value;
            submitBtn.disabled = false;
            updateSummary();
          });
          slotsBox.appendChild(btn);
        });
      })
      .catch(function () {
        slotsHint.textContent = "Could not load times. Please try again.";
      });
  }

  // ---- live booking summary ---------------------------------------------
  function updateSummary() {
    if (!summaryBox) return;
    const serviceCard = document.querySelector(
      '.choice-card[data-target="id_service"].selected'
    );
    const barberCard = document.querySelector(
      '.choice-card[data-target="id_barber"].selected'
    );
    const parts = [];
    if (serviceCard) parts.push(serviceCard.dataset.label);
    if (barberCard) parts.push("with " + barberCard.dataset.label);
    if (dateInput.value) parts.push("on " + dateInput.value);
    if (timeInput.value) parts.push("at " + timeInput.value);
    summaryBox.textContent = parts.length
      ? parts.join(" ")
      : "Your selection will appear here.";
  }

  // Pre-selected values (e.g. arriving from “Book with this barber”).
  document.querySelectorAll(".choice-card.preselected").forEach(function (card) {
    card.click();
  });
});
