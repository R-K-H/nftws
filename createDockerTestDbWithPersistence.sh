#For now a stateless instance for testing
docker run --rm -d --name postgres -e POSTGRES_USER=root -e POSTGRES_PASSWORD=toor -e POSTGRES_DB=nfts -p 5432:5432 -v /data/nftws/postgres:/var/lib/postgresql/data postgres 
