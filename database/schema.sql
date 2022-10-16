CREATE TABLE `solax_daily` (
  `uploadDate` date NOT NULL,
  `feed_in` float(6,1) DEFAULT NULL,
  `total_yield` float(6,1) DEFAULT NULL,
  PRIMARY KEY (`uploadDate`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `solax_local` (
  `uploadTime` datetime NOT NULL,
  `inverter_status` tinyint(4) DEFAULT NULL,
  `dc_solar_power` smallint(6) DEFAULT NULL,
  `grid_voltage_r` smallint(6) DEFAULT NULL,
  `grid_voltage_s` smallint(6) DEFAULT NULL,
  `grid_voltage_t` smallint(6) DEFAULT NULL,
  `battery_capacity` tinyint(4) DEFAULT NULL,
  `battery_power` smallint(6) DEFAULT NULL,
  `feed_in_power` smallint(6) DEFAULT NULL,
  `time_count_down` smallint(6) DEFAULT NULL,
  `inverter_ac_power` smallint(6) DEFAULT NULL,
  `consumeenergy` float(7,1) DEFAULT NULL,
  `feedinenergy` float(7,1) DEFAULT NULL,
  `power_dc1` smallint(6) DEFAULT NULL,
  `power_dc2` smallint(6) DEFAULT NULL,
  PRIMARY KEY (`uploadTime`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
