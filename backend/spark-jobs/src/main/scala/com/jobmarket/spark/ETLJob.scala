package com.jobmarket.spark

import org.apache.spark.sql.SparkSession

object ETLJob {
  def main(args: Array[String]): Unit = {
    val spark = SparkSession.builder()
      .appName("JobMarketETL")
      .getOrCreate()
    
    println("ETL Job started")
    spark.stop()
  }
}