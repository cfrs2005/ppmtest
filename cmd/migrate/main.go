package main

import (
	"log"

	"github.com/cfrs2005/ppmtest/internal/config"
	"github.com/cfrs2005/ppmtest/internal/database"
)

func main() {
	log.Println("Running database migrations...")

	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	db, err := database.New(&cfg.Database)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()

	if err := db.AutoMigrate(); err != nil {
		log.Fatalf("Failed to run migrations: %v", err)
	}

	log.Println("Migrations completed successfully")
}
