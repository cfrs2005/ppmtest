package models

import (
	"time"
)

// User represents a user in the system
type User struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	Username  string    `gorm:"size:50;uniqueIndex;not null" json:"username"`
	Email     string    `gorm:"size:100;uniqueIndex;not null" json:"email"`
	Password  string    `gorm:"size:255;not null" json:"-"`
	Role      string    `gorm:"size:20;default:author" json:"role"` // admin, author, subscriber
	Status    string    `gorm:"size:20;default:active" json:"status"` // active, inactive, banned
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`

	// Relations
	Posts     []Post     `gorm:"foreignKey:AuthorID" json:"posts,omitempty"`
	Comments  []Comment  `gorm:"foreignKey:AuthorID" json:"comments,omitempty"`
}
