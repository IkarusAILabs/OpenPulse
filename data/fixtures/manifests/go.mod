module example.com/sample-service

go 1.22

require (
    github.com/redis/go-redis/v9 v9.0.0
    golang.org/x/text v0.14.0 // indirect
    github.com/bad/entry v1.2.3-rc1
)

require github.com/stretchr/testify v1.9.0

replace example.com/local => ../local

retract v0.9.0
