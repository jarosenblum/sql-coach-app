Q1
SQL:::SELECT * FROM Customers;
RESULT:::Returned 91 rows with columns CustomerID, CustomerName, ContactName, Address, City, PostalCode, Country.
EXPLANATION:::This query selects all columns and rows from the Customers table.

Q2
SQL:::SELECT CustomerName, City FROM Customers;
RESULT:::Returned 91 rows with columns CustomerName and City.
EXPLANATION:::This query selects the CustomerName and City columns from the Customers table.

Q3
SQL:::SELECT * FROM Customers WHERE Country = 'Germany';
RESULT:::Returned 11 rows where Country is Germany.
EXPLANATION:::This query uses WHERE to filter customers from Germany.

Q4
SQL:::SELECT * FROM Customers WHERE Country = 'Germany' OR Country = 'France';
RESULT:::Returned rows where Country is Germany or France.
EXPLANATION:::This query uses OR to return customers from Germany or France.

Q5
SQL:::SELECT * FROM Customers ORDER BY CustomerName;
RESULT:::Returned 91 rows sorted by CustomerName.
EXPLANATION:::This query sorts all customer rows by CustomerName using ORDER BY.

Q6
SQL:::SELECT DISTINCT Country FROM Customers;
RESULT:::Returned unique country values from the Customers table.
EXPLANATION:::This query uses DISTINCT to return unique countries from Customers.

Q7
SQL:::SELECT COUNT(*) FROM Orders;
RESULT:::Returned 1 row with the total number of orders, 196.
EXPLANATION:::This query uses COUNT to return the total number of orders.

Q8
SQL:::SELECT Country, COUNT(*) FROM Customers GROUP BY Country;
RESULT:::Returned one row per country with a count of customers in each country.
EXPLANATION:::This query uses GROUP BY Country and COUNT to count customers in each country.

Q9
SQL:::SELECT Country, COUNT(*) FROM Customers GROUP BY Country HAVING COUNT(*) > 5;
RESULT:::Returned only countries whose customer count is greater than 5.
EXPLANATION:::This query uses HAVING with COUNT to filter grouped countries with more than 5 customers.

Q10
SQL:::SELECT Customers.CustomerName, Orders.OrderID FROM Customers JOIN Orders ON Customers.CustomerID = Orders.CustomerID;
RESULT:::Returned customer names with their order IDs by joining Customers and Orders on CustomerID.
EXPLANATION:::This query uses a JOIN between Customers and Orders on CustomerID to return CustomerName and OrderID.

Q11
SQL:::SELECT Customers.CustomerName, COUNT(Orders.OrderID) FROM Customers JOIN Orders ON Customers.CustomerID = Orders.CustomerID GROUP BY Customers.CustomerName;
RESULT:::Returned one row per customer with the count of orders made by each customer.
EXPLANATION:::This query uses a JOIN, GROUP BY, and COUNT to show how many orders each customer has made.