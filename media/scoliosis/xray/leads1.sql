-- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)
--
-- Host: localhost    Database: leads
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `client_data`
--

DROP TABLE IF EXISTS `client_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client_data` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(150) NOT NULL,
  `password` varchar(255) NOT NULL,
  `client_name` varchar(255) DEFAULT NULL,
  `business_name` varchar(255) DEFAULT NULL,
  `phone_number` varchar(20) DEFAULT NULL,
  `email` varchar(254) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `status` varchar(10) NOT NULL,
  `address` longtext,
  `gst` varchar(50) DEFAULT NULL,
  `logo` varchar(500) DEFAULT NULL,
  `website` varchar(200) DEFAULT NULL,
  `header_image` varchar(100) DEFAULT NULL,
  `quotation_footer_image` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_data`
--

LOCK TABLES `client_data` WRITE;
/*!40000 ALTER TABLE `client_data` DISABLE KEYS */;
INSERT INTO `client_data` VALUES (1,'8782788925','NAN8925@HE','Nandagopan Marar','Physio Clinic','8782788925','nandan_dummy@gmail.com','2025-12-17 16:15:25.017524','2025-12-22 12:40:11.895294','Active',NULL,NULL,NULL,NULL,NULL,NULL),(2,'9447742364','ANG2364@58','Angel Maria Kondody','Maria Kondody Travels','9447742364','kondodymotors_dummy@gmail.com','2025-12-17 17:03:59.621506','2025-12-22 12:40:49.687358','Active',NULL,NULL,NULL,NULL,NULL,NULL),(3,'8782788936','NAN8936@X3','Naveen','Naveen Textiles','8782788936','naveen-dumy@gmail.com','2025-12-18 09:38:03.161915','2025-12-22 12:39:54.743137','Active',NULL,NULL,NULL,NULL,NULL,NULL),(4,'8795788935','SON8935@W9','Sonu AB','Modern Roofing Pvt Ltd','8795788935','sonutech_dummy@gmail.com','2025-12-18 11:01:02.725412','2026-01-05 15:49:44.817527','Active','Erayil Kadavu,Kottayam','32AKZPM7513K1ZL','client_logos\\8795788935\\logo.jpg',NULL,'',''),(5,'8782788935','MER8935@5Z','Merin','Nexgen EHR','8782788935','tisser.tech_dummy@gmail.com','2025-12-18 12:18:11.023698','2025-12-20 15:33:23.790515','Active','Erayil Kadavu,Kottayam','32AKZPM7513K1ZL','client_logos\\8782788935\\logo.webp','https://nexgenehr.in',NULL,NULL),(6,'9787742365','MAR2365@FC','Maria Mathew','Varikkadan Travels','9787742365','varikkadan_dummy@gmail.com','2025-12-19 17:51:27.942089','2025-12-22 14:57:35.190648','Suspended','Kottayam','ASDFV14233S','client_logos\\9787742365\\logo.png',NULL,NULL,NULL),(7,'7256798923','ARU8923@5T','Arunima','ARM Stores','7256798923','arunima_dummy@gmail.com','2025-12-20 13:00:03.234756','2025-12-22 12:39:41.130986','Active',NULL,'32AKZPM7513K1ZL',NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `client_data` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `employee`
--

DROP TABLE IF EXISTS `employee`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `employee` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `employee_code` varchar(20) NOT NULL,
  `employee_name` varchar(100) NOT NULL,
  `gender` varchar(10) NOT NULL,
  `email` varchar(254) NOT NULL,
  `mobile` varchar(15) NOT NULL,
  `address` longtext,
  `designation` varchar(100) NOT NULL,
  `join_date` date NOT NULL,
  `status` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `client_id` bigint NOT NULL,
  `Password` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `employee_code` (`employee_code`),
  UNIQUE KEY `email` (`email`),
  KEY `Employee_client_id_fe4c438f_fk_client_data_id` (`client_id`),
  CONSTRAINT `Employee_client_id_fe4c438f_fk_client_data_id` FOREIGN KEY (`client_id`) REFERENCES `client_data` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `employee`
--

LOCK TABLES `employee` WRITE;
/*!40000 ALTER TABLE `employee` DISABLE KEYS */;
INSERT INTO `employee` VALUES (1,'SON000001','Sonu A B','Male','sonutech_dummy@gmail.com','8756341224','7th mile,Kottayam','Owner','2025-12-08',1,'2025-12-18 16:25:56.632769','2025-12-22 16:48:06.351573',4,'root'),(2,'SON000002','Ben Alex Thevalliparambil','Male','benalex_dummy@gmail.com','9856341224','Kottayam','Project Manager','2025-12-01',1,'2025-12-18 16:58:01.543443','2025-12-20 09:41:52.916016',4,'root'),(3,'SON000003','Manuel','Male','manuel@gmail.com','7683678212','Kottayam','Developer','2025-12-09',1,'2025-12-19 17:23:05.215507','2025-12-19 17:23:44.360627',4,'root'),(4,'SON000004','Samuel Johnson','Male','samuelj@gmail.com','9946341224','Kottayam','Jr Developer','2025-12-10',1,'2025-12-19 17:37:41.778684','2025-12-19 17:54:56.321186',4,'Samuel@9946'),(5,'SON000005','Simon Alex Thevalliparambil','Male','simon__dummy@gmail.com','9046341224','Ernakulam','Jr Developer','2025-12-18',1,'2025-12-22 10:57:45.920415','2025-12-22 10:59:56.875382',4,'root'),(6,'SON000006','Joseph Alex Thevalliparambil','Male','joseph__dummy@gmail.com','8399020210','Ernakulam','Jr Developer','2025-12-18',1,'2025-12-22 11:08:05.123537','2025-12-22 11:14:45.545625',4,'Joseph@123');
/*!40000 ALTER TABLE `employee` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `enquiryfor`
--

DROP TABLE IF EXISTS `enquiryfor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `enquiryfor` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `client_id` bigint NOT NULL,
  `status` varchar(10) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `EnquiryFor_client_id_name_38f02666_uniq` (`client_id`,`name`),
  CONSTRAINT `EnquiryFor_client_id_d52bddd2_fk_client_data_id` FOREIGN KEY (`client_id`) REFERENCES `client_data` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `enquiryfor`
--

LOCK TABLES `enquiryfor` WRITE;
/*!40000 ALTER TABLE `enquiryfor` DISABLE KEYS */;
INSERT INTO `enquiryfor` VALUES (1,'Logo','2025-12-22 16:12:06.891951','2025-12-22 16:34:36.083443',4,'Active'),(2,'Website','2025-12-22 16:34:21.833112','2025-12-22 16:34:21.833112',4,'Active'),(3,'Application','2025-12-22 17:19:41.855085','2025-12-22 17:19:41.855085',4,'Active'),(4,'Portfolio','2025-12-22 17:21:29.283884','2026-01-03 13:34:53.691855',4,'Active'),(5,'Videography','2025-12-22 17:21:45.283366','2025-12-22 17:21:45.283366',4,'Active'),(6,'Reels','2025-12-22 17:21:56.527184','2025-12-22 17:21:56.527184',4,'Active');
/*!40000 ALTER TABLE `enquiryfor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lead_app_document`
--

DROP TABLE IF EXISTS `lead_app_document`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lead_app_document` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `document_id` varchar(50) NOT NULL,
  `title` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `type` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `client_id` bigint NOT NULL,
  `expiry_date` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `document_id` (`document_id`),
  KEY `lead_app_document_client_id_a23adc36_fk_client_data_id` (`client_id`),
  CONSTRAINT `lead_app_document_client_id_a23adc36_fk_client_data_id` FOREIGN KEY (`client_id`) REFERENCES `client_data` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lead_app_document`
--

LOCK TABLES `lead_app_document` WRITE;
/*!40000 ALTER TABLE `lead_app_document` DISABLE KEYS */;
INSERT INTO `lead_app_document` VALUES (3,'LIC345773829','Enterprise License','bbdchsdhhbv hjdbvkrb','License','2026-01-05 10:35:30.111817',4,'2026-01-08'),(4,'LIC349773829','Pan Card','bvbbmvm','Document','2026-01-05 10:41:21.362030',4,'2026-01-10'),(5,'LIC342773829','License','vxxcvbb','License','2026-01-05 12:59:03.218558',4,'2026-02-06');
/*!40000 ALTER TABLE `lead_app_document` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lead_app_followup`
--

DROP TABLE IF EXISTS `lead_app_followup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lead_app_followup` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `lead_id` int NOT NULL,
  `client_id` int NOT NULL,
  `status` varchar(50) NOT NULL,
  `next_followup_date` date DEFAULT NULL,
  `next_followup_time` time(6) DEFAULT NULL,
  `converted_time` datetime(6) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lead_app_followup`
--

LOCK TABLES `lead_app_followup` WRITE;
/*!40000 ALTER TABLE `lead_app_followup` DISABLE KEYS */;
INSERT INTO `lead_app_followup` VALUES (1,1,4,'Follow-up','2026-01-08','16:00:00.000000','2026-01-03 13:55:12.645184','2026-01-03 13:55:12.645184'),(2,2,4,'Converted','2025-12-30','05:25:00.000000','2026-01-03 15:07:53.513792','2026-01-03 15:07:53.513792');
/*!40000 ALTER TABLE `lead_app_followup` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lead_app_followupremark`
--

DROP TABLE IF EXISTS `lead_app_followupremark`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lead_app_followupremark` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `lead_id` int NOT NULL,
  `client_id` int NOT NULL,
  `remark_date` date NOT NULL,
  `remark_text` varchar(500) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `followup_id_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `lead_app_followuprem_followup_id_id_e97a2545_fk_lead_app_` (`followup_id_id`),
  CONSTRAINT `lead_app_followuprem_followup_id_id_e97a2545_fk_lead_app_` FOREIGN KEY (`followup_id_id`) REFERENCES `lead_app_followup` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lead_app_followupremark`
--

LOCK TABLES `lead_app_followupremark` WRITE;
/*!40000 ALTER TABLE `lead_app_followupremark` DISABLE KEYS */;
INSERT INTO `lead_app_followupremark` VALUES (1,1,4,'2026-01-03','hjkb','2026-01-03 13:14:11.824105',1),(2,1,4,'2026-01-03','Add More beutiful images','2026-01-03 14:49:13.534473',1),(3,2,4,'2026-01-03','Accepted Good one','2026-01-03 15:06:27.100838',2),(4,1,4,'2026-01-05',',,m,m','2026-01-05 09:48:48.160535',1),(5,1,4,'2026-01-05','.m.m,m','2026-01-05 09:48:48.160535',1);
/*!40000 ALTER TABLE `lead_app_followupremark` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lead_app_quotation`
--

DROP TABLE IF EXISTS `lead_app_quotation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lead_app_quotation` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `client_name` varchar(200) NOT NULL,
  `client_phone` varchar(20) NOT NULL,
  `client_email` varchar(100) NOT NULL,
  `client_address` longtext NOT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  `gst_type` varchar(10) NOT NULL,
  `gst_amount` decimal(12,2) NOT NULL,
  `total` decimal(12,2) NOT NULL,
  `notes` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `client_id` bigint NOT NULL,
  `lead_id` bigint DEFAULT NULL,
  `valid_upto` date NOT NULL,
  `cgst` decimal(12,2) DEFAULT NULL,
  `igst` decimal(12,2) DEFAULT NULL,
  `sgst` decimal(12,2) DEFAULT NULL,
  `quotation_number` varchar(80) DEFAULT NULL,
  `version` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `lead_app_quotation_client_id_21f5a2f2_fk_client_data_id` (`client_id`),
  KEY `lead_app_quotation_lead_id_05a5cd50_fk_Lead_table_id` (`lead_id`),
  CONSTRAINT `lead_app_quotation_client_id_21f5a2f2_fk_client_data_id` FOREIGN KEY (`client_id`) REFERENCES `client_data` (`id`),
  CONSTRAINT `lead_app_quotation_lead_id_05a5cd50_fk_Lead_table_id` FOREIGN KEY (`lead_id`) REFERENCES `lead_table` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lead_app_quotation`
--

LOCK TABLES `lead_app_quotation` WRITE;
/*!40000 ALTER TABLE `lead_app_quotation` DISABLE KEYS */;
INSERT INTO `lead_app_quotation` VALUES (1,'Shyju Philip','9495213142','shyju@gmail.com','Erayil Kadavu,Kottayam',25750.00,'GST',4635.00,30385.00,'fdfg,mmf','2025-12-30 09:56:13.256537',4,1,'2025-12-18',2317.50,0.00,2317.50,'QUO-4_2025123000001','4'),(2,'Sabu','9674564635','sabu@gmail.com','Erumely,Kottayam',3000.00,'GST',540.00,3540.00,'Super','2025-12-30 14:28:55.217413',4,2,'2026-01-22',270.00,0.00,270.00,'QUO-4_2025123000002','2'),(3,'Shibu','7446545528','shibu@gmail.com','Erumely,Kottayam',17450.00,'GST',3141.00,20591.00,'Web Application ','2025-12-30 16:22:43.142907',4,3,'2026-01-05',1570.50,0.00,1570.50,'QUO-4_2025123000003','3');
/*!40000 ALTER TABLE `lead_app_quotation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lead_app_quotationitem`
--

DROP TABLE IF EXISTS `lead_app_quotationitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lead_app_quotationitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `quantity` int unsigned NOT NULL,
  `rate` decimal(10,2) NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `product_id` bigint NOT NULL,
  `quotation_id` bigint NOT NULL,
  `cgst` decimal(12,2) DEFAULT NULL,
  `igst` decimal(12,2) DEFAULT NULL,
  `sgst` decimal(12,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `lead_app_quotationitem_product_id_768ce1ec_fk_Product_id` (`product_id`),
  KEY `lead_app_quotationit_quotation_id_7c19c80b_fk_lead_app_` (`quotation_id`),
  CONSTRAINT `lead_app_quotationit_quotation_id_7c19c80b_fk_lead_app_` FOREIGN KEY (`quotation_id`) REFERENCES `lead_app_quotation` (`id`),
  CONSTRAINT `lead_app_quotationitem_product_id_768ce1ec_fk_Product_id` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`),
  CONSTRAINT `lead_app_quotationitem_chk_1` CHECK ((`quantity` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lead_app_quotationitem`
--

LOCK TABLES `lead_app_quotationitem` WRITE;
/*!40000 ALTER TABLE `lead_app_quotationitem` DISABLE KEYS */;
INSERT INTO `lead_app_quotationitem` VALUES (1,2,12000.00,24000.00,1,1,2160.00,NULL,2160.00),(2,2,1500.00,3000.00,3,2,270.00,NULL,270.00),(3,1,1500.00,1500.00,3,1,135.00,NULL,135.00),(4,1,5450.00,5450.00,2,3,490.50,NULL,490.50),(5,1,12000.00,12000.00,5,3,1080.00,NULL,1080.00),(7,1,250.00,250.00,2,1,22.50,NULL,22.50);
/*!40000 ALTER TABLE `lead_app_quotationitem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lead_table`
--

DROP TABLE IF EXISTS `lead_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lead_table` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `customer_name` varchar(150) NOT NULL,
  `phone` varchar(15) NOT NULL,
  `email` varchar(254) DEFAULT NULL,
  `address` longtext,
  `location` varchar(100) DEFAULT NULL,
  `product_category` varchar(100) NOT NULL,
  `lead_source_id` bigint NOT NULL,
  `requirement_details` longtext,
  `next_followup_date` date DEFAULT NULL,
  `followup_time` time(6) DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `remarks` longtext,
  `assign_to` varchar(100) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `client_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Lead_table_client_id_61c82500_fk_client_data_id` (`client_id`),
  KEY `Lead_table_lead_source_id_b7564021` (`lead_source_id`),
  CONSTRAINT `Lead_table_client_id_61c82500_fk_client_data_id` FOREIGN KEY (`client_id`) REFERENCES `client_data` (`id`),
  CONSTRAINT `Lead_table_lead_source_id_b7564021_fk_LeadSource_id` FOREIGN KEY (`lead_source_id`) REFERENCES `leadsource` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lead_table`
--

LOCK TABLES `lead_table` WRITE;
/*!40000 ALTER TABLE `lead_table` DISABLE KEYS */;
INSERT INTO `lead_table` VALUES (1,'Shyju Philip','9495213142','shyju@gmail.com','Erayil Kadavu,Kottayam',NULL,'Website',2,'Nice Logo with Web Application apt for enterprise','2026-01-08','16:00:00.000000','Follow-up',NULL,'Sonu A B','2025-12-19 13:41:10.579956','2026-01-05 09:50:08.862689',NULL,4),(2,'Sabu','9674564635','sabu@gmail.com','Erumely','Kottayam','Logo',4,NULL,'2025-12-30','05:25:00.000000','Converted',NULL,'Samuel Johnson','2025-12-22 15:27:01.702947','2026-01-03 15:07:53.517787',NULL,4),(3,'Shibu','7446545528','admin@shibu.com',NULL,'Ernakulam','Application',5,NULL,'2025-12-31','12:05:00.000000','Quoted',NULL,'Simon Alex Thevalliparambil','2025-12-23 13:04:00.372879','2026-01-02 10:05:30.694352',NULL,4),(4,'Byju Philip','9898953132','byju@gmail.com','Kottayam',NULL,'Application',6,NULL,'2025-12-17','21:37:00.000000','New',NULL,'Sonu A B','2025-12-30 16:37:27.384853','2026-01-06 11:01:45.464294',NULL,4),(5,'vnbnn','bmb','modernroofing23@gmail.com',NULL,'jkhjh','Logo',2,NULL,'2025-12-31',NULL,'New',NULL,NULL,'2025-12-31 10:53:21.288161','2025-12-31 14:31:34.675575',NULL,4),(6,'bm','6778798989',NULL,NULL,NULL,'Reels',2,NULL,'2026-01-28',NULL,'New',NULL,'Sonu A B','2025-12-31 10:53:52.370705','2026-01-06 15:08:11.397143',NULL,4);
/*!40000 ALTER TABLE `lead_table` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `leadsource`
--

DROP TABLE IF EXISTS `leadsource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leadsource` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `client_id` bigint NOT NULL,
  `status` varchar(10) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Lead_Source_client_id_28ad5b48_fk_client_data_id` (`client_id`),
  CONSTRAINT `Lead_Source_client_id_28ad5b48_fk_client_data_id` FOREIGN KEY (`client_id`) REFERENCES `client_data` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `leadsource`
--

LOCK TABLES `leadsource` WRITE;
/*!40000 ALTER TABLE `leadsource` DISABLE KEYS */;
INSERT INTO `leadsource` VALUES (2,'Manorama Weekly','2025-12-19 10:11:34.652659',4,'Active'),(4,'Online Website','2025-12-19 10:24:09.067020',4,'Active'),(5,'Visual Media','2025-12-19 10:29:32.196913',4,'Active'),(6,'CRM App','2025-12-19 10:36:15.937632',4,'Active'),(7,'Advertisement','2025-12-19 10:41:51.275495',4,'Active'),(8,'Social Media','2025-12-19 12:36:15.109815',5,'Active'),(13,'Advertisement','2025-12-22 10:16:16.958081',6,'Active'),(14,'Social Media','2025-12-22 10:18:39.093689',4,'Active');
/*!40000 ALTER TABLE `leadsource` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product`
--

DROP TABLE IF EXISTS `product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  `rate` decimal(10,2) NOT NULL,
  `gst_type` varchar(10) NOT NULL,
  `gst` decimal(5,2) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `client_id` bigint NOT NULL,
  `status` varchar(10) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Product_client_id_52f25a29_fk_client_data_id` (`client_id`),
  CONSTRAINT `Product_client_id_52f25a29_fk_client_data_id` FOREIGN KEY (`client_id`) REFERENCES `client_data` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product`
--

LOCK TABLES `product` WRITE;
/*!40000 ALTER TABLE `product` DISABLE KEYS */;
INSERT INTO `product` VALUES (1,'Roof Top Red',12000.00,'GST',18.00,'2025-12-19 11:11:53.805418','2025-12-22 15:00:04.869206',4,'Active'),(2,'Logo',13450.00,'GST',18.00,'2025-12-19 11:13:38.404787','2025-12-30 16:19:57.915009',4,'Active'),(3,'Welding set',1500.00,'GST',18.00,'2025-12-19 11:17:55.014876','2025-12-22 09:51:39.952682',4,'Active'),(4,'Website',1300.00,'GST',18.00,'2025-12-19 12:36:39.100037','2025-12-19 12:45:09.133716',5,'Active'),(5,'Website',12000.00,'GST',18.00,'2025-12-22 10:19:26.075001','2025-12-30 16:21:10.774233',4,'Active'),(6,'Icon',200.00,'GST',18.00,'2026-01-03 16:45:26.138473','2026-01-03 16:45:26.138473',4,'Active'),(7,'Web Socket',300.00,'GST',18.00,'2026-01-03 16:45:57.757720','2026-01-03 16:45:57.757720',4,'Active');
/*!40000 ALTER TABLE `product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'leads'
--

--
-- Dumping routines for database 'leads'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-06 17:17:23
