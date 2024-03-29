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

function daysInMonth(month, year) {
  return new Date(year, month, 0).getDate();
};

function generateWeeklySchedule() {

  var data = new FormData (); 
  var nowDate = new Date(); 
  var month = nowDate.getMonth()+1;
  var date = nowDate.getDate();

  if ( month.toString().length != 2 ) {
    month = '0'+month;
  };
  if ( date.length != 2 ) {
    date = '0'+date;
  };

  var today = nowDate.getFullYear() + '-'+ month + '-' + date;


  var daysInMonth = new Date(nowDate.getFullYear(), nowDate.getMonth(), 0).getDate();
  console.log(daysInMonth)

  for (let i=1; i <= daysInMonth; i++) {
    var data = new FormData ();
    var date = i;
    if ( date.toString().length != 2 ) {
      date = '0'+date;
    };
    var today = nowDate.getFullYear() + '-'+ month + '-' + date;
    data.append ("Date", today); 
    data.append ("Shift", "AM");

    fetch("/schedules", {
      method: "POST",
      body: data,
    });
  };

  for (let i=1; i <= daysInMonth; i++) {
    var data = new FormData ();
    var date = i;
    if ( date.toString().length != 2 ) {
      date = '0'+date;
    };
    var today = nowDate.getFullYear() + '-'+ month + '-' + date;
    data.append ("Date", today); 
    data.append ("Shift", "PM");

    fetch("/schedules", {
      method: "POST",
      body: data,
    }).then((_res) => {
      window.location.href = "/schedules";
  });
};
};

function deleteAllSchedules() {
  if (confirm("Delete all schedules?") == true) {
    fetch("/schedules/delete-all-schedules", {
      method: "POST",
    }).then((_res) => {
      window.location.href = "/schedules";
    });
  } else {
    window.location.href = "/schedules";
  }
};

