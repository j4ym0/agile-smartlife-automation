DROP TABLE IF EXISTS `tuya_devices`;
CREATE TABLE `tuya_devices` (
  `uid` int(11) NOT NULL,
  `id` varchar(100) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `dev_type` varchar(100) DEFAULT NULL,
  `ha_type` varchar(100) DEFAULT NULL,
  `dev_data` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

DROP TABLE IF EXISTS `tuya_accounts`;
CREATE TABLE `tuya_accounts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(100) NOT NULL,
  `password` varchar(100) NOT NULL,
  `access_token` varchar(100) DEFAULT NULL,
  `refresh_token` varchar(100) DEFAULT NULL,
  `expires` datetime DEFAULT '1970-01-01 00:00:00',
  PRIMARY KEY (`id`),
  UNIQUE KEY `tuya_accounts_UN` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
