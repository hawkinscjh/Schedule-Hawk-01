function deleteSchedule(schedule_id) {
  fetch("/schedules/delete-schedule", {
    method: "POST",
    body: JSON.stringify({ schedule_id: schedule_id }),
  }).then((_res) => {
    window.location.href = "/schedules";
  });
}
