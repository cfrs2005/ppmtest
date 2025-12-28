package models

import (
	"time"
)

// Post represents a blog post
type Post struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	Title       string    `gorm:"size:255;not null" json:"title"`
	Slug        string    `gorm:"size:255;uniqueIndex;not null" json:"slug"`
	Content     string    `gorm:"type:text" json:"content"`
	Summary     string    `gorm:"type:text" json:"summary"`
	Status      string    `gorm:"size:20;default:draft" json:"status"` // draft, published, archived
	AuthorID    uint      `gorm:"not null" json:"author_id"`
	ViewCount   int       `gorm:"default:0" json:"view_count"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
	PublishedAt *time.Time `json:"published_at,omitempty"`
}

// Comment represents a comment on a post
type Comment struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	PostID    uint      `gorm:"not null;index" json:"post_id"`
	AuthorID  uint      `gorm:"not null" json:"author_id"`
	Content   string    `gorm:"type:text;not null" json:"content"`
	Status    string    `gorm:"size:20;default:pending" json:"status"` // pending, approved, spam
	CreatedAt time.Time `json:"created_at"`
}

// Tag represents a tag for posts
type Tag struct {
	ID        uint   `gorm:"primaryKey" json:"id"`
	Name      string `gorm:"size:100;uniqueIndex;not null" json:"name"`
	Slug      string `gorm:"size:100;uniqueIndex;not null" json:"slug"`
}

// Category represents a category for posts
type Category struct {
	ID          uint   `gorm:"primaryKey" json:"id"`
	Name        string `gorm:"size:100;not null" json:"name"`
	Slug        string `gorm:"size:100;uniqueIndex;not null" json:"slug"`
	Description string `gorm:"type:text" json:"description"`
}
