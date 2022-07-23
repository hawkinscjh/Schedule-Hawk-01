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
    fetch("/schedules/"+schedule_id+"/profiles/"+profile_id, {
      method: "PUT",
      body: JSON.stringify({ schedule_id: schedule_id, profile_id: profile_id }),
    }).then((_res) => {
      window.location.href = "/schedules/"+schedule_id;
    });
};

function deleteScheduleProfile(schedule_id, profile_id) {
  if (confirm("Remove profile from schedule?") == true) {
  fetch("/schedules/"+schedule_id+"/profiles/"+profile_id, {
    method: "POST",
    body: JSON.stringify({ schedule_id: schedule_id, profile_id: profile_id }),
  }).then((_res) => {
    window.location.href = "/schedules/"+schedule_id;
  });
 } else {
  window.location.href = "/schedules/"+schedule_id;
}
};

function deleteRequestOff(profile_id, schedule_id) {
  if (confirm("Remove request off from profile?") == true) {
    console.log(Date);
  fetch("/profiles/delete-requestoff/"+profile_id, {
    method: "POST",
    body: JSON.stringify({ profile_id: profile_id, schedule_id: schedule_id}),
    
  }).then((_res) => {
    
    window.location.href = "/profiles/requestoffs/"+profile_id;
  });
 } else {
  window.location.href = "/profiles/requestoffs/"+profile_id;
}
};

function generateWeeklySchedule() {
    today = Date();
    console.log(today);
    fetch("/schedules", {
      method: "POST",
      body: JSON.stringify({ 'Date': 2022-07-22, 'Shift': "AM" }),
    }).then((_res) => {
      window.location.href = "/schedules";
  });
};