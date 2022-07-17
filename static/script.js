function deleteSchedule(schedule_id) {
  if (confirm("Delete schedule?") == true) {
    fetch("/schedules/delete-schedule", {
      method: "POST",
      body: JSON.stringify({ schedule_id: schedule_id }),
    }).then((_res) => {
      window.location.href = "/schedules";
    });
  } else {
    window.location.href = "/schedules";
  }
};

function deleteProfile(profile_id) {
  if (confirm("Delete user profile?") == true) {
    fetch("/profiles/delete-profile", {
      method: "POST",
      body: JSON.stringify({ profile_id: profile_id }),
    }).then((_res) => {
      window.location.href = "/profiles";
    });
  } else {
    window.location.href = "/profiles";
  }
};

function addScheduleProfile(schedule_id, profile_id) {
    fetch("/schedules/<schedule_id>/profiles/<profile_id>", {
      method: "PUT",
      body: JSON.stringify({ schedule_id: schedule_id, profile_id: profile_id }),
    }).then((_res) => {
      window.location.href = "/schedules/<schedule_id>";
    });
};
