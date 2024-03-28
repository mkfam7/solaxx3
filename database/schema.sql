CREATE TABLE solax_daily (
  uploadDate DATE NOT NULL,
  feed_in FLOAT NULL,
  total_yield FLOAT NULL
)
ENGINE=InnoDB
DEFAULT CHARSET=latin1;

CREATE TABLE solax_local (
  uploadTime DATETIME NOT NULL,
  inverter_status TINYINT NULL,
  dc_solar_power SMALLINT NULL,
  grid_voltage_r SMALLINT NULL,
  grid_voltage_s SMALLINT NULL,
  grid_voltage_t SMALLINT NULL,
  battery_capacity TINYINT NULL,
  battery_power SMALLINT NULL,
  feed_in_power SMALLINT NULL,
  time_count_down SMALLINT NULL,
  inverter_ac_power SMALLINT NULL,
  consumeenergy FLOAT NULL,
  feedinenergy FLOAT NULL,
  power_dc1 SMALLINT NULL,
  power_dc2 SMALLINT NULL,
  inv_volt_r SMALLINT NULL,
  inv_volt_s SMALLINT NULL,
  inv_volt_t SMALLINT NULL,
  off_grid_power_active_r INTEGER NULL,
  off_grid_power_active_s INTEGER NULL,
  off_grid_power_active_t INTEGER NULL,
  grid_power_r INTEGER NULL,
  grid_power_s INTEGER NULL,
  grid_power_t INTEGER NULL
)
ENGINE=InnoDB
DEFAULT CHARSET=latin1;